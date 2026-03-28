# Ruby via Magnus

Native Ruby extension built with Magnus. Requires Ruby 3.1+.

## Build & Test

```bash
cargo build
# Copy the shared library where Ruby can find it
cp target/debug/libalmide_mathlib.dylib almide_mathlib.bundle  # macOS
ruby test_mathlib.rb
```

## Notes

Ruby 2.6 (macOS system Ruby) is too old for Magnus. Install Ruby 3.1+ via rbenv or asdf.
