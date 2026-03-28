# Node.js via napi-rs

Native Node.js addon built with napi-rs.

## Build & Test

```bash
npm install
npx napi build --platform
node test_mathlib.cjs
```

## Notes

- `Point` is a plain JS object `{x, y}` via `#[napi(object)]` — no `new Point()` needed
- `Shape` is a class with `Shape.circle(r)` / `Shape.rect(w, h)` factory methods
- napi-rs auto-converts snake_case to camelCase (e.g. `safe_sqrt` → `safeSqrt`)
