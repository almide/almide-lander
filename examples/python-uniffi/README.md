# Python via UniFFI

Uses the same Cargo project as `swift-uniffi/`. UniFFI generates bindings for both languages from the same Rust source.

```bash
cd ../swift-uniffi
cargo build
cargo run --bin uniffi-bindgen generate --library target/debug/libalmide_mathlib.dylib --language python --out-dir ../python-uniffi/bindings
cp target/debug/libalmide_mathlib.dylib ../python-uniffi/bindings/
cd ../python-uniffi/bindings
PYTHONPATH=. python3 ../test_mathlib.py
```
