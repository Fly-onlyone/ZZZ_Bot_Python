---
tags: [operations]
---

# Port Configuration

> Dev backend 8001, prod backend 8000, frontend always 3000 (dev) — split deliberately so dev and prod don't collide. These are *preferred* ports; both launchers fall back to a free port if the preferred one is taken.

## Source
- `backend/Bot.py` — `--port` default 8001
- `backend/utils/network.py` — `find_free_port(preferred)` socket probe (unit-tested in `backend/test/test_network.py`)
- `src-tauri/src/lib.rs` — `backend_port()` default 8000; `resolve_backend_port()` free-port fallback
- `frontend/.env.development` — `VITE_BACKEND_URL=http://127.0.0.1:8001`
- `frontend/src/config/constants.js` — fallback `http://127.0.0.1:8000`

## How it works
| Context | Backend | Frontend |
|---|---|---|
| `uv run python backend/Bot.py` | 8001 | 3000 (Vite, auto-spawned) |
| `tauri dev` | 8001 (manual `Bot.py --no-frontend`, set `ZZZ_DEV_BACKEND_PORT=8001`) | 3000 (Vite, manual) |
| Production exe | 8000 (Tauri sidecar) | Tauri WebView serves `frontend/dist/` |

`VITE_BACKEND_URL` resolves by load mode: `bun run dev` reads `.env.development` and gets 8001; `bun run build` does not load `.env.development`, so the constant in `constants.js` (8000) wins.

## Free-port fallback
The default port is the *preference*, not a guarantee — a lingering instance or another process on it no longer crashes startup:

- **Dev (`uv run python backend/Bot.py`, not Tauri-hosted):** `find_free_port()` probes 8001; on `OSError` it binds port 0 and uses that for both uvicorn and the Vite `VITE_BACKEND_URL`. A warning logs the fallback port. `--hosted-by-tauri` runs bind `--port` exactly (the host already chose it).
- **Production exe:** `resolve_backend_port()` (release only — debug keeps the fixed dev port) probes 8000; on conflict it allocates a free port, stores it in `AppRuntime.backend_port`, and threads the *same* value to the sidecar `--port` and `backend_url`. The WebView learns the real URL via the `window.__ZZZ_BACKEND_URL__` global injected by the Rust-built main window (see [[Backend Port Resolution]], [[Frontend Constants]]).

Because the port can fall outside 8000/8001, the Tauri CSP `connect-src`/`img-src` allow any loopback port (`http://127.0.0.1:*`, `http://localhost:*`) — see [[Tauri]].

## Depends on
- [[Frontend Env Resolver]]
- [[Backend Port Resolution]]

## Used by
- [[Dev Server Architecture]]
- [[Production Build Pipeline]]

## See also
- [[_index]]
- [[Bot Dev Run]]
