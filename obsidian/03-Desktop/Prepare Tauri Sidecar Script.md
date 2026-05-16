---
tags: [desktop]
---

# Prepare Tauri Sidecar Script

> Bun TypeScript script that runs PyInstaller, detects the host Rust target triple, and copies the binary to `src-tauri/binaries/zzz-backend-{target}.exe` so Tauri can pick it up.

## Source
- `frontend/scripts/prepare-tauri-sidecar.ts` — primary

## How it works
1. Ensures `product/dist/` and `src-tauri/binaries/` exist.
2. Runs `uv run --group dev pyinstaller product/BotSidecar.spec --distpath product/dist --workpath product/build-sidecar --noconfirm` (inherits stdio; exits on failure).
3. Detects the host target via `rustc --print host-tuple` (e.g. `x86_64-pc-windows-msvc`).
4. Copies `product/dist/zzz-backend.exe` to `src-tauri/binaries/zzz-backend-{target}.exe` — the suffix is what `tauri_plugin_shell::sidecar("zzz-backend")` looks for at runtime.

Invoked via `bun run tauri:prepare-sidecar` (defined in `frontend/package.json`) before `cargo tauri build`.

## Depends on
- [[Bun]] — script runtime
- [[PyInstaller Sidecar Build]] — the spec it runs
- [[uv]] — invokes pyinstaller

## Used by
- [[Production Build Pipeline]]
- [[Sidecar Build]]

## See also
- [[_index]]
- [[Sidecar Spawn]]
