---
tags: [operations]
---

# Dev Server Architecture

> Dev uses two processes — Python backend on 8001 and Vite frontend on 3000 — talking via REST and SSE, intentionally split from prod ports so both can run side-by-side.

## Source
- `backend/Bot.py` — default `--port 8001`
- `frontend/vite.config.js` — dev server on 3000
- `src-tauri/src/lib.rs` — prod backend port 8000

## How it works
`uv run python backend/Bot.py` spawns FastAPI/Uvicorn on 8001 and also starts the Vite dev server on 3000 (auto-opens a browser at `http://localhost:3000`). Vite reads `frontend/.env.development` to get `VITE_BACKEND_URL=http://127.0.0.1:8001`, so the React app talks to the dev backend.

Running `tauri dev` in parallel uses 8001 too — the Rust shell skips spawning the sidecar when `ZZZ_DEV_BACKEND_PORT=8001` is set. The packaged exe runs on 8000 (Tauri sidecar) and frontend is served from `frontend/dist/`, so dev and prod never collide.

## Depends on
- [[Bot Entry Point]]
- [[Port Configuration]]
- [[Frontend Env Resolver]]

## Used by
- [[Bot Dev Run]]
- [[Tauri Dev Run]]

## See also
- [[_index]]
- [[Production Build Pipeline]]
