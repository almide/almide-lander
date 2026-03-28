# almide-lander

CLI tool for exporting Almide modules to other languages.

Depends on [almide-bindgen](https://github.com/almide/almide-bindgen) as an Almide library.

## Project Structure

```
almide-lander/
├── almide.toml       ← [dependencies] bindgen
├── almide.lock
├── src/
│   └── main.almd     ← import bindgen → CLI entry point
├── almide-lander.jpeg
├── README.md
├── CLAUDE.md
└── LICENSE
```

## Usage

```bash
almide run src/main.almd -- --lang python mylib.almd
```

## Git Commit Rules

- Commit messages must be in English
- Keep messages concise (1 line)
- No prefix (feat:, fix:, etc.)
