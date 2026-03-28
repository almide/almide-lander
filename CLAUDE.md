# almide-lander

Cross-Language Package Lander — CLI tool for exporting Almide modules to other languages.

Depends on [almide-bindgen](https://github.com/almide/almide-bindgen) (library).

## Project Structure

```
almide-lander/
├── almide.toml              ← [dependencies] bindgen = { git = "..." }
├── src/
│   └── main.almd            ← CLI entry point (import bindgen)
├── generators/              ← Legacy standalone generators (reference)
├── examples/                ← Example outputs for each language
├── sample/                  ← Sample Almide library for testing
├── almide-lander.jpeg       ← Hero image
├── README.md
├── CLAUDE.md
└── LICENSE
```

## Relationship

```
almide-bindgen (library)     →  almide-lander (CLI tool)
  src/mod.almd                     src/main.almd
  src/scaffolding.almd               import bindgen
  src/bindings/*.almd                 CLI args → bindgen calls
```

## Git Commit Rules

- Commit messages must be in English
- Keep messages concise (1 line)
- No prefix (feat:, fix:, etc.)
