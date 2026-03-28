# Sample: mathlib

The Almide source and its compiled outputs used by all examples.

## Files

| File | What | How to generate |
|------|------|-----------------|
| `mathlib.almd` | Almide source | (hand-written) |
| `interface.json` | Module Interface | `almide mathlib.almd --emit-interface` |
| `mathlib.rs` | Generated Rust | `almide mathlib.almd --target rust` |
| `mathlib.wasm` | Generated WASM | `almide build mathlib.almd --target wasm` |
