---
tags: [operations]
---

# Production Build Pipeline

> Three steps: build the React frontend, package the Python sidecar, then run `cargo tauri build` to produce the NSIS installer.

## Source
- `frontend/package.json`
- `frontend/scripts/prepare-sidecar.js`
- `src-tauri/tauri.conf.json`

## How it works
```bash
cd frontend
bun run build                  # Vite → frontend/dist/
bun run tauri:prepare-sidecar  # PyInstaller → src-tauri/binaries/zzz-bot-<triple>.exe
cd ..
cargo tauri build              # Bundles dist/ + sidecar into NSIS installer
```

`bun run build` reads `.env.production` (or its absence) so `VITE_BACKEND_URL` falls back to `http://127.0.0.1:8000` — the prod sidecar port. `prepare-sidecar` calls PyInstaller and renames the output with the correct Rust [[Target Triple Term]] so Tauri picks it up. `cargo tauri build` then bundles `frontend/dist/` plus the sidecar exe into a single NSIS installer.

## Depends on
- [[Sidecar Build]]
- [[NSIS Installer Build]]
- [[Prepare Tauri Sidecar Script]]

## Used by
- [[Sidecar Lifecycle]]

## See also
- [[_index]]
- [[Port Configuration]]
