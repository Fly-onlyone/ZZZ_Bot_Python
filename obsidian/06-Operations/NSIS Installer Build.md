---
tags: [operations]
---

# NSIS Installer Build

> `cargo tauri build` wraps the React bundle plus the PyInstaller sidecar into a single Windows NSIS installer.

## Source
- `src-tauri/tauri.conf.json` — `bundle.targets = ["nsis"]`
- `src-tauri/Cargo.toml`

## How it works
Run from the repo root after the frontend and sidecar are built:

```bash
cargo tauri build
```

Tauri compiles the Rust shell, picks up `frontend/dist/` and the renamed sidecar binary from `src-tauri/binaries/`, then invokes the bundled NSIS toolchain to produce the installer in `src-tauri/target/release/bundle/nsis/`.

The installer creates an `output/` directory next to the installed `.exe` so user data ([[Output Files]]) lives outside the program directory and survives upgrades — the [[Resource Path Resolution Pattern]] depends on this layout.

## Depends on
- [[Tauri]]
- [[NSIS]]
- [[NSIS Installer Config]]

## Used by
- [[Production Build Pipeline]]

## See also
- [[_index]]
- [[Sidecar Build]]
