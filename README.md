<p align="center">
  <img src="almide-lander.jpeg" alt="almide-lander" width="480" />
</p>

<h1 align="center">almide-lander</h1>

<p align="center">
  <strong>Cross-Language Package Lander</strong><br>
  Export Almide modules as native packages for Python, JS/TS, Swift, Ruby, C, and more.
</p>

<p align="center">
  <a href="https://github.com/almide/almide">Almide Compiler</a> ·
  <a href="https://github.com/almide/playground">Playground</a> ·
  <a href="#how-it-works">How It Works</a>
</p>

---

## What is this?

Write a library in [Almide](https://github.com/almide/almide). Run one command. Get a native package for any language.

```bash
almide-lander mathlib.almd --lang python   # → pip wheel
almide-lander mathlib.almd --lang js       # → npm package
almide-lander mathlib.almd --lang swift    # → Swift module
almide-lander mathlib.almd --lang ruby     # → gem
almide-lander mathlib.almd --lang c        # → .so + .h
```

No runtime. No VM. No engine. The output is a native module that runs at full speed in the target language. Almide disappears — only the compiled code remains.

## Demo

```almide
import math

type Point = { x: Float, y: Float }

type Shape =
  | Circle(Float)
  | Rect(Float, Float)

// Euclidean distance between two points.
fn distance(a: Point, b: Point) -> Float = {
  let dx = a.x - b.x
  let dy = a.y - b.y
  math.sqrt(dx * dx + dy * dy)
}

fn area(shape: Shape) -> Float = match shape {
  Circle(r) => math.pi() * r * r,
  Rect(w, h) => w * h,
}
```

Then use it from any language:

**Python**
```python
from almide_mathlib import Point, Shape, distance, area

d = distance(Point(x=0, y=0), Point(x=3, y=4))  # 5.0
a = area(Shape.circle(5.0))                       # 78.54
```

**JavaScript**
```javascript
const { distance, area, Shape } = require('almide-mathlib');

distance({x: 0, y: 0}, {x: 3, y: 4});  // 5.0
area(Shape.circle(5.0));                  // 78.54
```

**Swift**
```swift
let d = distance(a: Point(x: 0, y: 0), b: Point(x: 3, y: 4))  // 5.0
let a = area(shape: Shape.circle(radius: 5.0))                   // 78.54
```

**C**
```c
double d = almide_distance(0, 0, 3, 4);  // 5.0
double a = almide_area_circle(5.0);       // 78.54
```

## How It Works

```
mathlib.almd
     │
     ├─ almide --emit-interface → interface.json (types + functions + docs)
     ├─ almide --target rust    → Rust source
     └─ almide --target wasm    → WASM binary
            │
     almide-lander reads interface.json + compiled output
            │
            ├── Python:  Rust + PyO3 annotations → maturin → .whl
            ├── Node.js: Rust + napi-rs annotations → napi build → .node
            ├── Swift:   Rust + UniFFI annotations → uniffi-bindgen → .swift
            ├── JS/TS:   WASM + generated glue + .d.ts → npm package
            ├── C:       Rust + extern "C" + repr(C) → .so + .h
            └── Ruby:    Rust + Magnus annotations → gem
```

### The Module Interface

The Almide compiler extracts the public API into a language-agnostic JSON description:

```bash
almide mathlib.almd --emit-interface
```

```json
{
  "module": "mathlib",
  "types": [
    { "name": "Point", "kind": { "kind": "record", "fields": [
      { "name": "x", "type": { "kind": "float" } },
      { "name": "y", "type": { "kind": "float" } }
    ]}, "doc": "A 2D point with x and y coordinates." }
  ],
  "functions": [
    { "name": "distance",
      "params": [
        { "name": "a", "type": { "kind": "named", "name": "Point" } },
        { "name": "b", "type": { "kind": "named", "name": "Point" } }
      ],
      "return": { "kind": "float" },
      "doc": "Euclidean distance between two points.",
      "examples": ["distance(Point(0.0, 0.0), Point(3.0, 4.0)) == 5.0"]
    }
  ]
}
```

This JSON is the **stable contract** between the compiler and every binding generator. Almide-lander reads it to generate language-specific wrappers.

### Type Mapping

| Almide | Python | TypeScript | Swift | C | Ruby |
|--------|--------|------------|-------|---|------|
| `Int` | `int` | `number` | `Int64` | `int64_t` | `Integer` |
| `Float` | `float` | `number` | `Double` | `double` | `Float` |
| `String` | `str` | `string` | `String` | `char*` | `String` |
| `Bool` | `bool` | `boolean` | `Bool` | `bool` | `true/false` |
| `List[T]` | `list[T]` | `T[]` | `[T]` | — | `Array` |
| `Option[T]` | `T \| None` | `T \| null` | `T?` | nullable | `T \| nil` |
| `Record` | `@dataclass` | `interface` | `struct` | `struct` | `Struct` |
| `Variant` | `enum` | `union` | `enum` | tagged union | `class` |

### Two Paths

**Native path** (PyO3, napi-rs, Magnus, UniFFI): Almide → Rust source → language-specific binding annotations → native extension. Full speed, no overhead.

**WASM path** (JS/TS): Almide → WASM binary → JS glue + TypeScript declarations. Runs in any JS runtime (browser, Node, Deno, Bun).

## Verified Languages

| Language | Path | Status | How |
|----------|------|--------|-----|
| Python | PyO3 (native) | **verified** | `maturin build` → `.whl` |
| Python | UniFFI (native) | **verified** | auto-generated ctypes bridge |
| Swift | UniFFI (native) | **verified** | native Swift types |
| Node.js | napi-rs (native) | **verified** | `.node` addon |
| JS/TS | WASM (Deno) | **verified** | `.wasm` + `.d.ts` |
| C | cdylib (native) | **verified** | `.so` + `.h` |
| Ruby | Magnus (native) | code ready | needs Ruby 3.1+ |
| Kotlin | UniFFI | supported | via uniffi-bindgen |
| Go | UniFFI | supported | via uniffi-bindgen-go |
| C# | UniFFI | supported | via uniffi-bindgen-cs |
| Dart | UniFFI | supported | via uniffi-rs-dart |

## Why Not Just Write Rust?

If a human is writing the code, Rust is great. But if an **LLM** is generating the library:

- Almide's syntax eliminates borrowing, lifetimes, trait bounds, and macro complexity
- LLMs produce correct Almide code in fewer attempts than Rust
- The compiled output is identical — same `rustc` optimizations, same machine code
- One command packages it for any ecosystem

**Almide is what you get when you design a language for AI to write and compile to native speed.**

## Status

Early development. The Module Interface (`--emit-interface`) is stable and ships with the Almide compiler. The binding generators are proven via end-to-end tests but not yet packaged as a standalone tool.

## License

MIT
