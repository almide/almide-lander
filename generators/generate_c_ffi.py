"""
Generate C FFI wrapper: read interface.json + mathlib.rs -> extern "C" lib + C header.

Patterns:
  - Record types  -> #[repr(C)] struct, params flattened to scalars, returns via out-pointer
  - Variant types -> flattened to one extern "C" fn per case (C has no sum types)
  - String return -> *const c_char (caller frees with almide_free_string)
  - Scalars       -> passed/returned directly
"""
import json
import argparse
import os

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
ap = argparse.ArgumentParser(description="Generate C FFI wrapper from Almide interface")
ap.add_argument("--interface", default="interface.json", help="Path to interface.json")
ap.add_argument("--rust-src", default="mathlib.rs", help="Path to Almide-generated Rust source")
ap.add_argument("--out-dir", default=".", help="Output directory (writes src/lib.rs, Cargo.toml, header)")
args = ap.parse_args()

with open(args.interface) as f:
    iface = json.load(f)

with open(args.rust_src) as f:
    rust_source = f.read()

module = iface["module"]
lib_name = f"almide_{module}"
out_dir = args.out_dir

# ---------------------------------------------------------------------------
# Type helpers
# ---------------------------------------------------------------------------
type_defs = {t["name"]: t for t in iface["types"]}

C_TYPE_MAP = {"float": "double", "int": "int64_t", "bool": "int", "string": "const char*"}
RUST_FROM_C = {"double": "f64", "int64_t": "i64", "int": "i32", "const char*": "*const c_char"}


def c_scalar_type(tref):
    """Map Almide TypeRef to C type for scalars, or None if not scalar."""
    return C_TYPE_MAP.get(tref["kind"])


def is_scalar(tref):
    return tref["kind"] in C_TYPE_MAP


def is_record(tref):
    return tref["kind"] == "named" and tref["name"] in type_defs and type_defs[tref["name"]]["kind"]["kind"] == "record"


def is_variant(tref):
    return tref["kind"] == "named" and tref["name"] in type_defs and type_defs[tref["name"]]["kind"]["kind"] == "variant"


def record_fields(name):
    return type_defs[name]["kind"]["fields"]


def variant_cases(name):
    return type_defs[name]["kind"]["cases"]


def flatten_record_params(prefix, rec_name):
    """Flatten record into (c_arg_name, c_type) pairs for scalar fields."""
    result = []
    for f in record_fields(rec_name):
        ft = f["type"]
        arg_name = f"{prefix}{f['name']}"
        if is_scalar(ft):
            result.append((arg_name, c_scalar_type(ft)))
        elif is_record(ft):
            result.extend(flatten_record_params(f"{arg_name}_", ft["name"]))
        else:
            result.append((arg_name, "void*"))
    return result


def build_reconstruct_record(prefix, rec_name):
    """Rust expression reconstructing an Almide record from flat C args."""
    parts = []
    for f in record_fields(rec_name):
        ft = f["type"]
        arg = f"{prefix}{f['name']}"
        if is_record(ft):
            inner = build_reconstruct_record(f"{arg}_", ft["name"])
            parts.append(f"{f['name']}: {inner}")
        else:
            parts.append(f"{f['name']}: {arg}")
    return f"{rec_name} {{ {', '.join(parts)} }}"


# ---------------------------------------------------------------------------
# Expand each interface function into one or more extern "C" signatures.
#
# If a function takes a variant param, it is flattened: one extern fn per case.
# Otherwise a single extern fn is produced.
# Returns list of dicts: {extern_name, flat_params:[(name, c_type)], ret, call_str}
# ---------------------------------------------------------------------------
def expand_function(fn_def):
    fname = fn_def["name"]
    ret = fn_def["return"]
    variant_params = [(i, p) for i, p in enumerate(fn_def["params"]) if is_variant(p["type"])]

    if not variant_params:
        flat = []
        call_args = []
        for p in fn_def["params"]:
            pt = p["type"]
            if is_record(pt):
                flat.extend(flatten_record_params(p["name"], pt["name"]))
                call_args.append(build_reconstruct_record(p["name"], pt["name"]))
            elif is_scalar(pt):
                flat.append((p["name"], c_scalar_type(pt)))
                call_args.append(p["name"])
        return [{"extern_name": f"almide_{fname}", "flat_params": flat, "ret": ret,
                 "call_str": f"{fname}({', '.join(call_args)})"}]

    # Variant expansion: one fn per case
    assert len(variant_params) == 1, "Multiple variant params not yet supported"
    vi, vparam = variant_params[0]
    vtype_name = vparam["type"]["name"]
    cases = variant_cases(vtype_name)
    other_params = [(i, p) for i, p in enumerate(fn_def["params"]) if i != vi]

    results = []
    for case in cases:
        case_lower = case["name"].lower()
        flat = []
        call_args_indexed = {}  # position -> call_arg string

        for oi, op in other_params:
            pt = op["type"]
            if is_record(pt):
                flat.extend(flatten_record_params(op["name"], pt["name"]))
                call_args_indexed[oi] = build_reconstruct_record(op["name"], pt["name"])
            elif is_scalar(pt):
                flat.append((op["name"], c_scalar_type(pt)))
                call_args_indexed[oi] = op["name"]

        payload_args = []
        if case.get("payload") and case["payload"]["kind"] == "tuple":
            for fi, ft in enumerate(case["payload"]["fields"]):
                ct = c_scalar_type(ft) or "double"
                arg_name = f"v{fi}"
                flat.append((arg_name, ct))
                payload_args.append(arg_name)

        if payload_args:
            variant_expr = f"{vtype_name}::{case['name']}({', '.join(payload_args)})"
        else:
            variant_expr = f"{vtype_name}::{case['name']}"
        call_args_indexed[vi] = variant_expr

        call_args = [call_args_indexed[i] for i in sorted(call_args_indexed)]
        results.append({"extern_name": f"almide_{fname}_{case_lower}", "flat_params": flat,
                         "ret": ret, "call_str": f"{fname}({', '.join(call_args)})"})
    return results


# ---------------------------------------------------------------------------
# Emit Rust wrapper for a single expanded function
# ---------------------------------------------------------------------------
def emit_rust_fn(spec):
    lines = []
    params = []
    for name, ct in spec["flat_params"]:
        rtype = RUST_FROM_C.get(ct, "f64")
        params.append(f"{name}: {rtype}")

    ret = spec["ret"]
    if is_record(ret):
        params.append(f"out: *mut C{ret['name']}")

    params_str = ", ".join(params)

    if ret["kind"] == "string":
        lines.append(f"#[no_mangle]")
        lines.append(f"pub extern \"C\" fn {spec['extern_name']}({params_str}) -> *const c_char {{")
        lines.append(f"    let s = {spec['call_str']};")
        lines.append(f"    CString::new(s).unwrap().into_raw() as *const c_char")
        lines.append(f"}}")
    elif is_record(ret):
        lines.append(f"#[no_mangle]")
        lines.append(f"pub extern \"C\" fn {spec['extern_name']}({params_str}) {{")
        lines.append(f"    let r = {spec['call_str']};")
        lines.append(f"    unsafe {{")
        for f in record_fields(ret["name"]):
            lines.append(f"        (*out).{f['name']} = r.{f['name']};")
        lines.append(f"    }}")
        lines.append(f"}}")
    else:
        rtype = RUST_FROM_C.get(c_scalar_type(ret), "f64")
        lines.append(f"#[no_mangle]")
        lines.append(f"pub extern \"C\" fn {spec['extern_name']}({params_str}) -> {rtype} {{")
        lines.append(f"    {spec['call_str']}")
        lines.append(f"}}")
    return lines


# ---------------------------------------------------------------------------
# Emit C header declaration for a single expanded function
# ---------------------------------------------------------------------------
def emit_header_decl(spec):
    ret = spec["ret"]
    c_params = [f"{ct} {name}" for name, ct in spec["flat_params"]]

    if is_record(ret):
        c_ret = "void"
        c_params.append(f"{ret['name']}* out")
    elif ret["kind"] == "string":
        c_ret = "const char*"
    else:
        c_ret = c_scalar_type(ret) or "double"

    params_str = ", ".join(c_params) if c_params else "void"
    return f"{c_ret} {spec['extern_name']}({params_str});"


# ---------------------------------------------------------------------------
# Build all expanded specs
# ---------------------------------------------------------------------------
all_specs = []
for fn_def in iface["functions"]:
    all_specs.extend(expand_function(fn_def))

# ---------------------------------------------------------------------------
# Generate src/lib.rs
# ---------------------------------------------------------------------------
rs = []
rs.append("// AUTO-GENERATED by generate_c_ffi.py -- do not edit")
rs.append("use std::ffi::CString;")
rs.append("use std::os::raw::c_char;")
rs.append("")

# Include Almide-generated Rust (stripped of boilerplate)
for line in rust_source.split("\n"):
    if line.startswith("#![allow"):
        continue
    if line.startswith("use std::collections"):
        continue
    if "fn main(" in line:
        continue
    rs.append(line)
rs.append("")

# #[repr(C)] structs for record types
for t in iface["types"]:
    if t["kind"]["kind"] == "record":
        name = t["name"]
        rs.append("#[repr(C)]")
        rs.append(f"pub struct C{name} {{")
        for f in t["kind"]["fields"]:
            ct = c_scalar_type(f["type"]) or "double"
            rtype = RUST_FROM_C.get(ct, "f64")
            rs.append(f"    pub {f['name']}: {rtype},")
        rs.append("}")
        rs.append("")

# Free-string helper
rs.append("/// Free a string returned by an almide C FFI function.")
rs.append("#[no_mangle]")
rs.append('pub extern "C" fn almide_free_string(s: *mut c_char) {')
rs.append("    if s.is_null() { return; }")
rs.append("    unsafe { drop(CString::from_raw(s)); }")
rs.append("}")
rs.append("")

for spec in all_specs:
    rs.extend(emit_rust_fn(spec))
    rs.append("")

# ---------------------------------------------------------------------------
# Generate Cargo.toml
# ---------------------------------------------------------------------------
cargo = f"""\
[package]
name = "almide-{module}-c"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "staticlib"]
name = "{lib_name}"
"""

# ---------------------------------------------------------------------------
# Generate C header
# ---------------------------------------------------------------------------
h = []
h.append("/* AUTO-GENERATED by generate_c_ffi.py -- do not edit */")
h.append(f"#ifndef {lib_name.upper()}_H")
h.append(f"#define {lib_name.upper()}_H")
h.append("")
h.append("#include <stdint.h>")
h.append("")

for t in iface["types"]:
    if t["kind"]["kind"] == "record":
        name = t["name"]
        h.append("typedef struct {")
        for f in t["kind"]["fields"]:
            ct = c_scalar_type(f["type"]) or "double"
            h.append(f"    {ct} {f['name']};")
        h.append(f"}} {name};")
        h.append("")

h.append("void almide_free_string(char* s);")
h.append("")

for spec in all_specs:
    h.append(emit_header_decl(spec))

h.append("")
h.append(f"#endif /* {lib_name.upper()}_H */")
h.append("")

# ---------------------------------------------------------------------------
# Write output files
# ---------------------------------------------------------------------------
src_dir = os.path.join(out_dir, "src")
os.makedirs(src_dir, exist_ok=True)

with open(os.path.join(src_dir, "lib.rs"), "w") as f:
    f.write("\n".join(rs) + "\n")

with open(os.path.join(out_dir, "Cargo.toml"), "w") as f:
    f.write(cargo)

with open(os.path.join(out_dir, f"{lib_name}.h"), "w") as f:
    f.write("\n".join(h) + "\n")

print(f"Generated: src/lib.rs, Cargo.toml, {lib_name}.h")
