---
tags: [operations]
---

# Port Configuration

> Dev backend 8001, prod backend 8000, frontend always 3000 (dev) — split deliberately so dev and prod don't collide.

## Source
- `backend/Bot.py` — `--port` default 8001
- `src-tauri/src/lib.rs` — `backend_port()` default 8000
- `frontend/.env.development` — `VITE_BACKEND_URL=http://127.0.0.1:8001`
- `frontend/src/config/constants.js` — fallback `http://127.0.0.1:8000`

## How it works
| Context | Backend | Frontend |
|---|---|---|
| `uv run python backend/Bot.py` | 8001 | 3000 (Vite, auto-spawned) |
| `tauri dev` | 8001 (manual `Bot.py --no-frontend`, set `ZZZ_DEV_BACKEND_PORT=8001`) | 3000 (Vite, manual) |
| Production exe | 8000 (Tauri sidecar) | Tauri WebView serves `frontend/dist/` |

`VITE_BACKEND_URL` resolves by load mode: `bun run dev` reads `.env.development` and gets 8001; `bun run build` does not load `.env.development`, so the constant in `constants.js` (8000) wins.

## Depends on
- [[Frontend Env Resolver]]
- [[Backend Port Resolution]]

## Used by
- [[Dev Server Architecture]]
- [[Production Build Pipeline]]

## See also
- [[_index]]
- [[Bot Dev Run]]
