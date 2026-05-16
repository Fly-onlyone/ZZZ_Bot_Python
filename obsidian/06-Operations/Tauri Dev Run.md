---
tags: [operations]
---

# Tauri Dev Run

> `bun run tauri:app` plus a manually-started `Bot.py --no-frontend` — exercises the desktop shell against a hand-launched backend so you can iterate on the native window without rebuilding the sidecar.

## Source
- `src-tauri/tauri.conf.json`
- `frontend/package.json` — `tauri:app` script
- `src-tauri/src/lib.rs` — `backend_port()` resolver

## How it works
The Tauri dev shell expects the backend already running. Workflow:

1. Terminal 1 — `uv run python backend/Bot.py --no-frontend` (backend on 8001, no Vite).
2. Terminal 2 — `cd frontend && bun run dev` (Vite on 3000).
3. Terminal 3 — `set ZZZ_DEV_BACKEND_PORT=8001 && bun run tauri:app` (or `cargo tauri dev`).

`ZZZ_DEV_BACKEND_PORT=8001` tells the Rust shell to skip spawning its own sidecar and just point the WebView at the dev backend.

## Depends on
- [[Tauri]]
- [[Tauri Shell Entry]]
- [[Backend Port Resolution]]

## Used by
- [[Dev Server Architecture]]

## Gotchas
- Forgetting `ZZZ_DEV_BACKEND_PORT` makes the shell try to start a second backend on 8000 and fail because the sidecar binary doesn't exist in dev.

## See also
- [[_index]]
- [[Bot Dev Run]]
- [[Sidecar Spawn]]
