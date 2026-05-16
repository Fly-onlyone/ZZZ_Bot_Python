---
tags: [integration]
---

# FastAPI

> ASGI web framework hosting the REST API + Server-Sent Events stream that the frontend (and the Tauri shell) talk to.

## Used for
- All `/shopping`, `/redeem`, `/account`, `/settings`, `/overview/*`, `/manual`, `/locator-tracker`, `/backup/*`, `/tasks/*`, `/shutdown`, `/routes` endpoints
- SSE event bus for live task progress (see [[SSE Event Bus Pattern]])

## Configuration
- Version `fastapi==0.120.4` (`pyproject.toml`)
- `starlette==0.49.3` pinned for compatibility
- App instance lives on [[GlobalVar]]
- Port default 8001 in dev (`Bot.py --port`), 8000 in production (Tauri sidecar)

## Wire-up
- `backend/core/Bot.py` — instantiates `FastAPI()`, registers lifespan, mounts routes
- `backend/api/routes.py` — all REST + SSE endpoints
- `backend/core/Event Bus.py` — publishes events to SSE subscribers

## Auth mode
- Open on `127.0.0.1` (CSP-locked from the frontend)
- Privileged endpoints (`/shutdown`, `/tasks/run-playwright`) require the `x-desktop-token` header — see [[Desktop Token]]

## Gotchas
- CORS-free because everything is `127.0.0.1` + CSP-pinned; if you ever expose externally, you must add CORS middleware and tighten auth.

## See also
- [[_index]]
- [[Uvicorn]]
- [[Bot Entry Point]]
