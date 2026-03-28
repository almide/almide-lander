# JS/TS via WASM (Deno)

TypeScript wrapper over Almide WASM binary. Runs in any JS runtime (Deno, Node, browser).

## Build & Test

```bash
# Copy WASM binary from sample
cp ../../sample/mathlib.wasm .

# Run with Deno
deno run --allow-read test_mathlib.ts
```

## Notes

- WASI stubs are auto-generated from module imports
- Point: 16 bytes `[f64 x][f64 y]`, little-endian
- Shape: tagged union `[i32 tag][f64... payload]`
- String: length-prefixed `[i32 len][u8... bytes]`
