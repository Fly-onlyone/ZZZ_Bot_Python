---
tags: [integration]
---

# Tauri

> Rust desktop shell that hosts the React frontend in a native WebView, owns the tray icon, manages window state, and spawns/babysits the Python backend as a sidecar.

## Used for
- Native window + tray icon (see [[Tray Menu]])
- Bundling the React `dist/` as the WebView source
- Spawning the Python sidecar (see [[Sidecar Spawn]])
- Autostart registration via `tauri-plugin-autostart`
- NSIS installer packaging (see [[NSIS Installer Config]])

## Configuration
- Version `tauri = "2.11.2"` with `features = ["tray-icon"]` (`src-tauri/Cargo.toml`)
- Build: `tauri-build = "2.5.4"`
- Plugins: `tauri-plugin-single-instance = "2"`, `tauri-plugin-shell = "2"`, `tauri-plugin-autostart = "2"`, `tauri-plugin-log = "2"`
- Bundle target: `nsis`, install mode `currentUser`, install dir `%LOCALAPPDATA%\Programs\ZZZ Bot`
- CSP `connect-src`/`img-src` allow any loopback port (`http://127.0.0.1:*`, `http://localhost:*`) + Sentry ingest — widened from the old 8000/8001 lock so a free-port fallback still works (see [[Backend Port Resolution]])

## Wire-up
- `src-tauri/src/main.rs` — entry point stub
- `src-tauri/src/lib.rs` — builder + setup + run-event handlers
- `src-tauri/tauri.conf.json` — bundle + CSP config (no `app.windows`: the main window is built in `lib.rs` `setup()` so it can carry the URL-injecting `initialization_script`)

## Auth mode
N/A — Tauri itself; the sidecar IPC uses the [[Desktop Token]].

## See also
- [[_index]]
- [[Tauri Shell Entry]]
- [[NSIS]]
