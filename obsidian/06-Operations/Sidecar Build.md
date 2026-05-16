---
tags: [operations]
---

# Sidecar Build

> PyInstaller packs the Python backend into a single `.exe` named with the Rust target triple so Tauri's sidecar resolver finds it.

## Source
- `frontend/scripts/prepare-sidecar.js`
- `pyinstaller.spec` (or inline `pyinstaller` args)

## How it works
`bun run tauri:prepare-sidecar` invokes PyInstaller against `backend/Bot.py`, bundling the Python interpreter, all third-party packages, the `sample/` reference images, the `message/` Jinja2 templates, and Playwright's browser binaries. The output is renamed `zzz-bot-<target-triple>.exe` (e.g. `zzz-bot-x86_64-pc-windows-msvc.exe`) and dropped into `src-tauri/binaries/`. Tauri's `bundle.externalBin` config picks it up via the triple suffix at `cargo tauri build` time.

In exe mode, the Python entry point detects PyInstaller via `sys.frozen` and routes paths through [[Resource Path Resolution Pattern]].

## Depends on
- [[PyInstaller]]
- [[Target Triple Term]]
- [[Prepare Tauri Sidecar Script]]

## Used by
- [[Production Build Pipeline]]
- [[NSIS Installer Build]]

## Gotchas
- Rename must match the Rust triple exactly — Tauri's resolver is strict.
- Playwright browsers add ~150MB to the bundle.

## See also
- [[_index]]
- [[Sidecar Term]]
