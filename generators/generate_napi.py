"""
Generate a napi-rs Node.js addon from Almide compiler outputs.

Reads:
  - interface.json  (Almide module interface)
  - mathlib.rs      (Almide-generated Rust source)

Produces:
  - src/lib.rs      (Rust source with napi-rs annotations)
  - Cargo.toml
  - build.rs
  - package.json
"""
import argparse
import json
import os
import re


def resolve_default_path(filename):
    """Resolve an input file: try CWD first, then ../../sample/ relative to this script."""
    if os.path.exists(filename):
        return filename
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fallback = os.path.join(script_dir, "..", "sample", filename)
    if os.path.exists(fallback):
        return fallback
    return filename  # let it fail with a clear error


def parse_args():
    p = argparse.ArgumentParser(description="Generate napi-rs Node.js addon from Almide compiler output")
    p.add_argument("--interface", default=None, help="Path to interface.json (default: auto-detect)")
    p.add_argument("--rust-source", default=None, help="Path to generated Rust source (default: auto-detect)")
    p.add_argument("--outdir", default=".", help="Output directory (default: cwd)")
    args = p.parse_args()
    if args.interface is None:
        args.interface = resolve_default_path("interface.json")
    if args.rust_source is None:
        args.rust_source = resolve_default_path("mathlib.rs")
    return args


# ---------------------------------------------------------------------------
# Type mapping
# ---------------------------------------------------------------------------

def rust_type(tref):
    """Almide TypeRef -> Rust type string."""
    k = tref["kind"]
    if k == "float":  return "f64"
    if k == "int":    return "i64"
    if k == "string": return "String"
    if k == "bool":   return "bool"
    if k == "named":  return tref["name"]
    if k == "option": return f"Option<{rust_type(tref['inner'])}>"
    if k == "list":   return f"Vec<{rust_type(tref['inner'])}>"
    return "/* unknown */"


def js_type(tref):
    """Almide TypeRef -> TypeScript/JSDoc type hint."""
    k = tref["kind"]
    if k == "float":  return "number"
    if k == "int":    return "number"
    if k == "string": return "string"
    if k == "bool":   return "boolean"
    if k == "named":  return tref["name"]
    if k == "option": return f"{js_type(tref['inner'])} | null"
    if k == "list":   return f"Array<{js_type(tref['inner'])}>"
    return "any"


# ---------------------------------------------------------------------------
# Classify types from interface.json
# ---------------------------------------------------------------------------

def build_type_index(types):
    """Build lookup: type name -> kind ('record' or 'variant')."""
    idx = {}
    for t in types:
        idx[t["name"]] = t["kind"]["kind"]
    return idx


# ---------------------------------------------------------------------------
# Rust source rewriting
# ---------------------------------------------------------------------------

STRIP_LINE_PREFIXES = [
    "#![allow",
    "use std::collections",
    "fn main(",
]


def should_strip_line(line):
    return any(line.startswith(p) for p in STRIP_LINE_PREFIXES)


def extract_runtime_lines(rust_source):
    """Extract the runtime/support portion of mathlib.rs (everything before the
    first struct/enum definition), stripping preamble lines we don't want."""
    lines = rust_source.split("\n")
    result = []
    for line in lines:
        if should_strip_line(line):
            continue
        # Stop when we hit the first Almide type definition.
        # These are the #[derive(...)] lines that precede struct/enum.
        if line.startswith("#[derive(") and ("PartialEq" in line or "PartialOrd" in line):
            break
        result.append(line)
    # Trim trailing blank lines
    while result and result[-1].strip() == "":
        result.pop()
    return result


def extract_function_body(rust_source, fname):
    """Extract the body of a pub fn from the Almide-generated Rust source.
    Returns the full text from 'pub fn <name>' through the matching closing brace."""
    # Match the function start -- handles both single-line and multi-line bodies
    pattern = rf'pub fn {re.escape(fname)}\('
    match = re.search(pattern, rust_source)
    if not match:
        return None
    start = match.start()
    # Walk forward to find the balanced closing brace
    depth = 0
    i = start
    found_open = False
    while i < len(rust_source):
        ch = rust_source[i]
        if ch == '{':
            depth += 1
            found_open = True
        elif ch == '}':
            depth -= 1
            if found_open and depth == 0:
                return rust_source[start:i + 1]
        i += 1
    return None


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def generate_lib_rs(iface, rust_source, type_index):
    """Generate the full src/lib.rs content."""
    types = iface["types"]
    functions = iface["functions"]
    variant_names = {t["name"] for t in types if t["kind"]["kind"] == "variant"}

    lines = []
    lines.append("#![allow(unused_parens, unused_variables, dead_code, unused_imports, unused_mut, unused_must_use)]")
    lines.append("")
    lines.append("use napi_derive::napi;")
    lines.append("")

    # --- Runtime support code ---
    runtime = extract_runtime_lines(rust_source)
    if runtime:
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("// Almide runtime (inlined from codegen)")
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("")
        lines.extend(runtime)
        lines.append("")

    # --- Type definitions ---
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("// Almide-generated types (adapted for napi)")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("")

    for t in types:
        name = t["name"]
        doc = t.get("doc", "")
        kind = t["kind"]["kind"]

        if kind == "record":
            fields = t["kind"]["fields"]
            if doc:
                lines.append(f"/// {doc}")
            lines.append(f"/// napi(object) makes this a plain JS object.")
            lines.append(f"#[napi(object)]")
            lines.append(f"#[derive(Clone, Debug)]")
            lines.append(f"pub struct {name} {{")
            for fld in fields:
                lines.append(f"    pub {fld['name']}: {rust_type(fld['type'])},")
            lines.append(f"}}")
            lines.append("")

        elif kind == "variant":
            cases = t["kind"]["cases"]
            inner_name = f"{name}Inner"

            if doc:
                lines.append(f"/// Internal Rust enum for {name} -- not directly exposed to JS.")
            lines.append(f"#[derive(Clone, Debug)]")
            lines.append(f"enum {inner_name} {{")
            for case in cases:
                cname = case["name"]
                if case.get("payload") and case["payload"]["kind"] == "tuple":
                    pfields = case["payload"]["fields"]
                    tuple_types = ", ".join(rust_type(pf) for pf in pfields)
                    lines.append(f"    {cname}({tuple_types}),")
                else:
                    lines.append(f"    {cname},")
            lines.append(f"}}")
            lines.append("")

            if doc:
                lines.append(f"/// {doc}")
            lines.append(f"#[napi]")
            lines.append(f"pub struct {name} {{")
            lines.append(f"    inner: {inner_name},")
            lines.append(f"}}")
            lines.append("")

            lines.append(f"#[napi]")
            lines.append(f"impl {name} {{")
            for case in cases:
                cname = case["name"]
                factory_name = cname.lower()
                if case.get("payload") and case["payload"]["kind"] == "tuple":
                    pfields = case["payload"]["fields"]
                    params = ", ".join(f"v{i}: {rust_type(pf)}" for i, pf in enumerate(pfields))
                    args = ", ".join(f"v{i}" for i in range(len(pfields)))
                    lines.append(f"    /// Create a {factory_name}.")
                    lines.append(f"    #[napi(factory)]")
                    lines.append(f"    pub fn {factory_name}({params}) -> {name} {{")
                    lines.append(f"        {name} {{")
                    lines.append(f"            inner: {inner_name}::{cname}({args}),")
                    lines.append(f"        }}")
                    lines.append(f"    }}")
                    lines.append("")
                else:
                    lines.append(f"    /// Create a {factory_name}.")
                    lines.append(f"    #[napi(factory)]")
                    lines.append(f"    pub fn {factory_name}() -> {name} {{")
                    lines.append(f"        {name} {{")
                    lines.append(f"            inner: {inner_name}::{cname},")
                    lines.append(f"        }}")
                    lines.append(f"    }}")
                    lines.append("")
            lines.append(f"}}")
            lines.append("")

    # --- Function wrappers ---
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("// Almide-generated functions (wrapped for napi)")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append("")

    for fn_def in functions:
        fname = fn_def["name"]
        doc = fn_def.get("doc", "")
        ret = fn_def["return"]

        # Extract function body from the Almide-generated source
        body_text = extract_function_body(rust_source, fname)
        if body_text is None:
            lines.append(f"// WARNING: could not extract body for {fname}")
            lines.append("")
            continue

        # Rewrite the function for napi
        if doc:
            lines.append(f"/// {doc}")
        lines.append(f"#[napi]")

        # Build parameter list
        param_strs = []
        for p in fn_def["params"]:
            ptype = p["type"]
            pname = p["name"]
            if ptype["kind"] == "named" and ptype["name"] in variant_names:
                # Variant types: pass by reference to the napi class
                param_strs.append(f"{pname}: &{ptype['name']}")
            else:
                param_strs.append(f"{pname}: {rust_type(ptype)}")
        params_str = ", ".join(param_strs)

        ret_type = rust_type(ret)
        lines.append(f"pub fn {fname}({params_str}) -> {ret_type} {{")

        # Extract the inner body (between outermost braces)
        body_inner = extract_body_inner(body_text)
        # Rewrite the body for napi types
        rewritten = rewrite_body_for_napi(body_inner, fn_def, variant_names, type_index)
        lines.append(rewritten)

        lines.append(f"}}")
        lines.append("")

    return "\n".join(lines)


def extract_body_inner(fn_text):
    """Given a full 'pub fn ...' text, extract the code inside the outermost braces."""
    # Find the first opening brace
    idx = fn_text.index('{')
    depth = 0
    start = idx + 1
    for i in range(idx, len(fn_text)):
        if fn_text[i] == '{':
            depth += 1
        elif fn_text[i] == '}':
            depth -= 1
            if depth == 0:
                return fn_text[start:i].strip()
    return fn_text[start:].strip()


def rewrite_body_for_napi(body, fn_def, variant_names, type_index):
    """Rewrite function body to work with napi types.

    Key transformations:
    - For variant params: `param.clone()` -> `param.inner.clone()`
    - For variant params: `TypeName::Variant(...)` -> `TypeNameInner::Variant(...)`
    - Remove `.clone()` on record params (napi passes owned values)
    """
    result = body

    for p in fn_def["params"]:
        ptype = p["type"]
        pname = p["name"]
        if ptype["kind"] == "named" and ptype["name"] in variant_names:
            vname = ptype["name"]
            # param.clone() -> param.inner.clone()
            result = result.replace(f"{pname}.clone()", f"{pname}.inner.clone()")
            # TypeName::Case -> TypeNameInner::Case in match arms
            result = re.sub(
                rf'\b{re.escape(vname)}::',
                f'{vname}Inner::',
                result,
            )

    # Indent the body
    indented = []
    for line in result.split("\n"):
        stripped = line.strip()
        if stripped:
            indented.append(f"    {stripped}")
        else:
            indented.append("")
    return "\n".join(indented)


def generate_cargo_toml(module_name):
    """Generate Cargo.toml for the napi-rs crate."""
    # napi crate names use hyphens
    crate_name = f"almide-{module_name}"
    return f"""[package]
name = "{crate_name}"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
napi = {{ version = "2", features = ["default"] }}
napi-derive = "2"

[build-dependencies]
napi-build = "2"

[profile.release]
lto = true
"""


def generate_build_rs():
    """Generate build.rs for napi-build."""
    return """extern crate napi_build;

fn main() {
    napi_build::setup();
}
"""


def generate_package_json(module_name):
    """Generate package.json for the napi-rs package."""
    pkg_name = f"almide-{module_name}"
    return json.dumps({
        "name": pkg_name,
        "version": "0.1.0",
        "main": "index.js",
        "napi": {
            "name": pkg_name,
            "triples": {},
        },
        "devDependencies": {
            "@napi-rs/cli": "^2",
        },
    }, indent=2) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    with open(args.interface) as f:
        iface = json.load(f)

    with open(args.rust_source) as f:
        rust_source = f.read()

    module_name = iface["module"]
    type_index = build_type_index(iface["types"])

    outdir = args.outdir

    # Generate src/lib.rs
    lib_rs = generate_lib_rs(iface, rust_source, type_index)
    src_dir = os.path.join(outdir, "src")
    os.makedirs(src_dir, exist_ok=True)
    with open(os.path.join(src_dir, "lib.rs"), "w") as f:
        f.write(lib_rs)

    # Generate Cargo.toml
    with open(os.path.join(outdir, "Cargo.toml"), "w") as f:
        f.write(generate_cargo_toml(module_name))

    # Generate build.rs
    with open(os.path.join(outdir, "build.rs"), "w") as f:
        f.write(generate_build_rs())

    # Generate package.json
    with open(os.path.join(outdir, "package.json"), "w") as f:
        f.write(generate_package_json(module_name))

    print(f"Generated: src/lib.rs, Cargo.toml, build.rs, package.json")


if __name__ == "__main__":
    main()
