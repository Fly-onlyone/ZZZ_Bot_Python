---
tags: [backend, api]
---

# Health Endpoints

> Liveness, run-status, manual-control state, log retrieval, and the SSE event stream consumed by the frontend.

## Source
- `backend/api/routes.py` — primary

## How it works
- `GET /health` returns `get_startup_status()` so the frontend can gate boot until the backend is ready.
- `GET /check-run-status` reads `last_run` from SQLite and recomputes `next_run` via `bot_runtime.calculate_next_run()`.
- `GET /playstate` reports [[ManualLoginManager]] state plus a boolean `playState` for the manual login page.
- `GET /logs` parses rotated `app.log*` files via a regex line matcher; supports `date`, `level`, `search`, `limit`, `offset` query params and tolerates traceback continuation lines. Path is resolved through [[Resource Path Resolution Pattern]] in exe mode.
- `GET /events` is the [[SSE Term]] stream. Each client gets a queue from [[Event Bus]] `subscribe()`; events are yielded as `event: <type>\ndata: <payload>\n\n` with a 30-second keepalive comment. Powers [[useTaskEvents]] and the live status surfaces.

## Depends on
- [[Event Bus]] — backs `/events`
- [[Logger]] — log format the parser expects
- [[ManualLoginManager]] — `/playstate`

## Used by
- [[Frontend Data Flow]] — startup gate and live updates
- [[Logs Page]] — `/logs`
- [[useTaskEvents]] — `/events`

## See also
- [[_index]]
- [[SSE Event Bus Pattern]]
