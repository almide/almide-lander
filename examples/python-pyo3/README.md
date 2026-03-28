# Python via PyO3

Native Python extension built with PyO3 + maturin.

## Build & Test

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install maturin
maturin develop
python3 test_mathlib.py
```

## How it was generated

```bash
almide mathlib.almd --emit-interface > interface.json
almide mathlib.almd --target rust > mathlib.rs
python3 ../../generators/generate_pyo3.py  # reads interface.json + mathlib.rs → src/lib.rs + .pyi
```
