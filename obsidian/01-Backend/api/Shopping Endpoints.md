---
tags: [backend, api]
---

# Shopping Endpoints

> CRUD over shopping selections plus a derived view of hunt-mode timing for the overview surface.

## Source
- `backend/api/routes.py` — primary

## How it works
- `GET /shopping` returns the raw shopping document from [[DataStore]] (`Selected`, `Hunt`, `Item's list`).
- `POST /shopping` replaces `Selected` and `Hunt` arrays then calls `bot_runtime.schedule_hunt_tasks()` so [[Schedule]] picks up the new hunt windows immediately.
- `GET /overview/hunt` joins the hunt list against `Item's list` to produce per-item scheduled times. Countdown strings (`hh:mm:ss`) are converted to absolute return times via `calculate_return_time()` in [[StringUtil]], then offset by `HuntModeHandler.WAIT_BUFFER_SECONDS` to compute the actual scheduled hunt time. Returns `{enabled, hunt_items, next_hunt_time}` where `enabled` is true only when both `settings.run_task` and `settings.enable_hunt_mode` are true.

## Depends on
- [[DataStore]] — `get_shopping`, `save_shopping`
- [[HuntModeHandler]] — `WAIT_BUFFER_SECONDS`, `get_hunt_items`, `get_next_hunt_time`
- [[StringUtil]] — `calculate_return_time`

## Used by
- [[Shopping Page]] — selection editor
- [[Hunt Section]] — timing display

## See also
- [[_index]]
- [[Hunt Mode Lifecycle]]
