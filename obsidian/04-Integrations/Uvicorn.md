---
tags: [integration]
---

# Uvicorn

> ASGI server that hosts the FastAPI app; runs in-process inside the same Python sidecar that runs the scheduler and Playwright tasks.

## Used for
- Serving the REST API on `127.0.0.1:{port}`
- Hosting the SSE stream
- Single-process colocation with `schedule` polling and Playwright work

## Configuration
- Version `uvicorn==0.38.0` (`pyproject.toml`)
- Host `127.0.0.1`, port from `--port` arg (default 8001 dev / 8000 prod)
- `wsproto>=1.3.2` declared but not actively used (WebSocket placeholder)

## Wire-up
- `backend/core/Bot.py` — `uvicorn.Config(app, host="127.0.0.1", port=...)` + `Server(config).serve()` started on an asyncio loop

## Auth mode
N/A (loopback only)

## Gotchas
- Run on a dedicated asyncio task so the scheduler poll loop on a separate thread can keep firing; never use `uvicorn.run()` blocking helper here.

## See also
- [[_index]]
- [[FastAPI]]
- [[Bot Entry Point]]
