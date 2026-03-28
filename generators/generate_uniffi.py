"""
Generate UniFFI-annotated Rust crate from Almide interface.json + mathlib.rs.

Produces:
  - src/lib.rs   (Rust source with UniFFI proc macro annotations)
  - Cargo.toml
  - uniffi-bindgen.rs

Usage:
  python generate_uniffi.py [--interface FILE] [--source FILE] [--out-dir DIR] [--crate-name NAME]
"""
import argparse
import json
import os
import re
import textwrap

# ── Almide runtime inlining ──
# Maps almide_rt_* function names to their inline Rust implementations.
# The generator scans the source for calls to these and emits only the ones used.
RUNTIME_INLINES = {
    "almide_rt_math_sin":       "fn almide_rt_math_sin(x: f64) -> f64 { x.sin() }",
    "almide_rt_math_cos":       "fn almide_rt_math_cos(x: f64) -> f64 { x.cos() }",
    "almide_rt_math_tan":       "fn almide_rt_math_tan(x: f64) -> f64 { x.tan() }",
    "almide_rt_math_asin":      "fn almide_rt_math_asin(x: f64) -> f64 { x.asin() }",
    "almide_rt_math_acos":      "fn almide_rt_math_acos(x: f64) -> f64 { x.acos() }",
    "almide_rt_math_atan":      "fn almide_rt_math_atan(x: f64) -> f64 { x.atan() }",
    "almide_rt_math_atan2":     "fn almide_rt_math_atan2(y: f64, x: f64) -> f64 { y.atan2(x) }",
    "almide_rt_math_log":       "fn almide_rt_math_log(x: f64) -> f64 { x.ln() }",
    "almide_rt_math_log2":      "fn almide_rt_math_log2(x: f64) -> f64 { x.log2() }",
    "almide_rt_math_log10":     "fn almide_rt_math_log10(x: f64) -> f64 { x.log10() }",
    "almide_rt_math_exp":       "fn almide_rt_math_exp(x: f64) -> f64 { x.exp() }",
    "almide_rt_math_pow":       "fn almide_rt_math_pow(base: i64, exp: i64) -> i64 { base.pow(exp as u32) }",
    "almide_rt_math_abs":       "fn almide_rt_math_abs(x: i64) -> i64 { x.abs() }",
    "almide_rt_math_ceil":      "fn almide_rt_math_ceil(x: f64) -> f64 { x.ceil() }",
    "almide_rt_math_floor":     "fn almide_rt_math_floor(x: f64) -> f64 { x.floor() }",
    "almide_rt_math_round":     "fn almide_rt_math_round(x: f64) -> f64 { x.round() }",
    "almide_rt_math_sqrt":      "fn almide_rt_math_sqrt(x: f64) -> f64 { x.sqrt() }",
    "almide_rt_math_pi":        "fn almide_rt_math_pi() -> f64 { std::f64::consts::PI }",
    "almide_rt_math_e":         "fn almide_rt_math_e() -> f64 { std::f64::consts::E }",
    "almide_rt_math_inf":       "fn almide_rt_math_inf() -> f64 { f64::INFINITY }",
    "almide_rt_math_is_nan":    "fn almide_rt_math_is_nan(x: f64) -> bool { x.is_nan() }",
    "almide_rt_math_min":       "fn almide_rt_math_min(a: i64, b: i64) -> i64 { a.min(b) }",
    "almide_rt_math_max":       "fn almide_rt_math_max(a: i64, b: i64) -> i64 { a.max(b) }",
    "almide_rt_math_sign":      "fn almide_rt_math_sign(n: i64) -> i64 { if n > 0 { 1 } else if n < 0 { -1 } else { 0 } }",
    "almide_rt_math_fmin":      "fn almide_rt_math_fmin(a: f64, b: f64) -> f64 { a.min(b) }",
    "almide_rt_math_fmax":      "fn almide_rt_math_fmax(a: f64, b: f64) -> f64 { a.max(b) }",
    "almide_rt_math_fpow":      "fn almide_rt_math_fpow(base: f64, exp: f64) -> f64 { base.powf(exp) }",
    "almide_rt_math_factorial":  textwrap.dedent("""\
        fn almide_rt_math_factorial(n: i64) -> i64 {
            (1..=n).product()
        }"""),
    "almide_rt_math_choose":    textwrap.dedent("""\
        fn almide_rt_math_choose(n: i64, k: i64) -> i64 {
            if k < 0 || k > n { return 0; }
            let k = k.min(n - k) as u64;
            let mut result: u64 = 1;
            for i in 0..k {
                result = result * (n as u64 - i) / (i + 1);
            }
            result as i64
        }"""),
    "almide_rt_math_log_gamma": textwrap.dedent("""\
        fn almide_rt_math_log_gamma(x: f64) -> f64 {
            let t = x + 6.5;
            (2.5066282746310005_f64).ln()
                + (x - 0.5) * t.ln()
                - t
                + (1.000000000190015
                    + 76.18009172947146 / x
                    + -86.50532032941677 / (x + 1.0)
                    + 24.01409824083091 / (x + 2.0)
                    + -1.231739572450155 / (x + 3.0)
                    + 0.001208650973866179 / (x + 4.0)
                    + -0.000005395239384953 / (x + 5.0))
                    .ln()
        }"""),
}


def rust_type(tref: dict) -> str:
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


def is_named_type(tref: dict) -> bool:
    """True if the type is a record or variant (passed by & in UniFFI)."""
    return tref["kind"] == "named"


def find_used_runtime_fns(source: str, iface: dict) -> list[str]:
    """Scan only user function bodies for almide_rt_* calls, return sorted unique names."""
    fn_names = [f["name"] for f in iface["functions"]]
    # Extract just the function body regions
    body_text = []
    for fname in fn_names:
        pattern = rf'pub fn {fname}\([^)]*\)\s*->\s*\S+\s*\{{(.+?)(?=\npub fn |\Z)'
        m = re.search(pattern, source, re.DOTALL)
        if m:
            body_text.append(m.group(1))
    combined = "\n".join(body_text)
    found = set(re.findall(r'almide_rt_\w+', combined))
    return sorted(found)


def extract_function_bodies(source: str, iface: dict) -> dict[str, str]:
    """
    Extract the Almide-generated function bodies from mathlib.rs, rewritten
    for UniFFI:
      - Record/variant params taken by &ref instead of by-value
      - .clone() on params replaced with field access (ref semantics)
      - Tuple variant patterns rewritten to named-field patterns
      - Struct construction stays the same (already named)
    """
    type_names = {t["name"] for t in iface["types"]}
    variant_types = {}  # name -> {case_name -> [field_names]}
    for t in iface["types"]:
        if t["kind"]["kind"] == "variant":
            cases = {}
            for case in t["kind"]["cases"]:
                if case.get("payload") and case["payload"]["kind"] == "tuple":
                    n = len(case["payload"]["fields"])
                    cases[case["name"]] = [f"v{i}" for i in range(n)]
                else:
                    cases[case["name"]] = []
            variant_types[t["name"]] = cases

    bodies = {}
    for fn_def in iface["functions"]:
        fname = fn_def["name"]
        # Find the function in source: `pub fn name(...)  ... `
        # The Almide codegen puts everything on one logical block.
        pattern = rf'pub fn {fname}\([^)]*\)\s*->\s*\S+\s*\{{(.+?)(?=\npub fn |\Z)'
        m = re.search(pattern, source, re.DOTALL)
        if not m:
            bodies[fname] = '    todo!("body not found in source")'
            continue

        raw = m.group(0)
        # Strip the signature -- we'll generate our own
        brace_start = raw.index('{')
        body = raw[brace_start + 1:].strip()
        # Remove trailing } that belongs to the function
        if body.endswith('}'):
            body = body[:-1].strip()

        # Rewrite tuple variant patterns to named-field patterns.
        # e.g. Shape::Circle(r) => ...  ->  Shape::Circle { v0: r } => ...
        # e.g. Shape::Rect(w, h) => ... ->  Shape::Rect { v0: w, v1: h } => ...
        for vtype, cases in variant_types.items():
            for cname, field_names in cases.items():
                if not field_names:
                    continue
                # Match: Type::Case(bindings)
                tuple_pat = rf'{vtype}::{cname}\(([^)]+)\)'
                def rewrite_match(m, _fnames=field_names, _vt=vtype, _cn=cname):
                    bindings = [b.strip() for b in m.group(1).split(',')]
                    pairs = ", ".join(
                        f"{fname}: {b}" for fname, b in zip(_fnames, bindings)
                    )
                    return f'{_vt}::{_cn} {{ {pairs} }}'
                body = re.sub(tuple_pat, rewrite_match, body)

        # Remove .clone() calls -- UniFFI passes &ref, field access works on refs
        body = body.replace('.clone()', '')

        # Indent each line
        indented = []
        for line in body.split('\n'):
            stripped = line.strip()
            if stripped:
                indented.append(f'    {stripped}')
        bodies[fname] = '\n'.join(indented)

    return bodies


def generate_lib_rs(iface: dict, source: str) -> str:
    """Generate src/lib.rs with UniFFI annotations."""
    lines = []
    lines.append("// Almide {} — UniFFI bindings (auto-generated from interface.json)".format(
        iface["module"]))
    lines.append("")

    # Runtime inlines -- only the ones actually called from user functions
    used_rt = find_used_runtime_fns(source, iface)
    if used_rt:
        lines.append("// ── Almide runtime (minimal subset) ──")
        lines.append("")
        for name in used_rt:
            if name in RUNTIME_INLINES:
                lines.append(RUNTIME_INLINES[name])
        lines.append("")

    # Types
    lines.append("// ── Types ──")
    lines.append("")
    for t in iface["types"]:
        name = t["name"]
        doc = t.get("doc", "")
        kind = t["kind"]["kind"]

        if kind == "record":
            if doc:
                lines.append(f"/// {doc}")
            lines.append(f"#[derive(Debug, Clone, uniffi::Record)]")
            lines.append(f"pub struct {name} {{")
            for field in t["kind"]["fields"]:
                lines.append(f"    pub {field['name']}: {rust_type(field['type'])},")
            lines.append("}")
            lines.append("")

        elif kind == "variant":
            if doc:
                lines.append(f"/// {doc}")
            lines.append(f"#[derive(Debug, Clone, uniffi::Enum)]")
            lines.append(f"pub enum {name} {{")
            for case in t["kind"]["cases"]:
                cname = case["name"]
                if case.get("payload") and case["payload"]["kind"] == "tuple":
                    pfields = case["payload"]["fields"]
                    field_decls = ", ".join(
                        f"v{i}: {rust_type(pf)}" for i, pf in enumerate(pfields)
                    )
                    lines.append(f"    {cname} {{ {field_decls} }},")
                else:
                    lines.append(f"    {cname},")
            lines.append("}")
            lines.append("")

    # Functions
    bodies = extract_function_bodies(source, iface)

    lines.append("// ── Functions ──")
    lines.append("")
    for fn_def in iface["functions"]:
        fname = fn_def["name"]
        doc = fn_def.get("doc", "")

        # Build parameter list: named types get & prefix
        params = []
        for p in fn_def["params"]:
            ptype = p["type"]
            rtype = rust_type(ptype)
            if is_named_type(ptype):
                params.append(f"{p['name']}: &{rtype}")
            else:
                params.append(f"{p['name']}: {rtype}")
        params_str = ", ".join(params)

        ret_type = rust_type(fn_def["return"])

        if doc:
            lines.append(f"/// {doc}")
        lines.append("#[uniffi::export]")
        lines.append(f"pub fn {fname}({params_str}) -> {ret_type} {{")

        body = bodies.get(fname, '    todo!()')
        lines.append(body)

        lines.append("}")
        lines.append("")

    # Scaffolding
    lines.append("uniffi::setup_scaffolding!();")
    lines.append("")

    return "\n".join(lines)


def generate_cargo_toml(crate_name: str, module_name: str) -> str:
    """Generate Cargo.toml for the UniFFI crate."""
    # Cargo lib name: underscores
    lib_name = crate_name.replace("-", "_")
    return textwrap.dedent(f"""\
        [package]
        name = "{crate_name}"
        version = "0.1.0"
        edition = "2021"

        [lib]
        crate-type = ["cdylib", "lib"]
        name = "{lib_name}"

        [dependencies]
        uniffi = {{ version = "0.28", features = ["cli"] }}

        [build-dependencies]
        uniffi = {{ version = "0.28", features = ["build"] }}

        [[bin]]
        name = "uniffi-bindgen"
        path = "uniffi-bindgen.rs"
    """)


def generate_uniffi_bindgen_rs() -> str:
    return "fn main() { uniffi::uniffi_bindgen_main() }\n"


def main():
    parser = argparse.ArgumentParser(
        description="Generate UniFFI-annotated Rust crate from Almide interface.json + source"
    )
    parser.add_argument("--interface", default="interface.json",
                        help="Path to interface.json (default: interface.json)")
    parser.add_argument("--source", default="mathlib.rs",
                        help="Path to Almide-generated Rust source (default: mathlib.rs)")
    parser.add_argument("--out-dir", default=".",
                        help="Output directory (default: current dir)")
    parser.add_argument("--crate-name", default=None,
                        help="Crate name (default: almide-<module>)")
    args = parser.parse_args()

    with open(args.interface) as f:
        iface = json.load(f)

    with open(args.source) as f:
        source = f.read()

    module = iface["module"]
    crate_name = args.crate_name or f"almide-{module}"
    out_dir = args.out_dir

    # Ensure output directories exist
    src_dir = os.path.join(out_dir, "src")
    os.makedirs(src_dir, exist_ok=True)

    # Generate files
    lib_rs = generate_lib_rs(iface, source)
    cargo_toml = generate_cargo_toml(crate_name, module)
    bindgen_rs = generate_uniffi_bindgen_rs()

    lib_path = os.path.join(src_dir, "lib.rs")
    cargo_path = os.path.join(out_dir, "Cargo.toml")
    bindgen_path = os.path.join(out_dir, "uniffi-bindgen.rs")

    with open(lib_path, "w") as f:
        f.write(lib_rs)
    with open(cargo_path, "w") as f:
        f.write(cargo_toml)
    with open(bindgen_path, "w") as f:
        f.write(bindgen_rs)

    lib_name = crate_name.replace("-", "_")
    print(f"Generated: {lib_path}")
    print(f"Generated: {cargo_path}")
    print(f"Generated: {bindgen_path}")
    print()
    print("Next steps:")
    print(f"  cd {out_dir}")
    print(f"  cargo build")
    print(f"  cargo run --bin uniffi-bindgen generate \\")
    print(f"    --library target/debug/lib{lib_name}.dylib \\")
    print(f"    --language swift --out-dir bindings")


if __name__ == "__main__":
    main()
