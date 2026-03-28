# C via cdylib

Shared library with `extern "C"` functions and `#[repr(C)]` structs.

## Build & Test

```bash
cargo build
cc test_mathlib.c -L target/debug -lalmide_mathlib -o test
DYLD_LIBRARY_PATH=target/debug ./test  # macOS
# LD_LIBRARY_PATH=target/debug ./test  # Linux
```
