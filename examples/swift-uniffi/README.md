# Swift via UniFFI

Native Swift module built with Mozilla UniFFI. Same Rust source also generates Python, Kotlin, and Ruby bindings.

## Build & Test

```bash
cargo build
cargo run --bin uniffi-bindgen generate --library target/debug/libalmide_mathlib.dylib --language swift --out-dir ./bindings

cd bindings
swiftc -import-objc-header almide_mathlibFFI.h \
  -L ../target/debug -lalmide_mathlib \
  almide_mathlib.swift ../test_mathlib.swift -o test
DYLD_LIBRARY_PATH=../target/debug ./test
```
