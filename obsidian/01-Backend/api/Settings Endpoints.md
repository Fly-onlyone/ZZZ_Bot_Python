---
tags: [backend, api]
---

# Settings Endpoints

> Read and update the shared settings document, with side effects on schedulers, Sentry runtime, and MongoDB connection.

## Source
- `backend/api/routes.py` — primary

## How it works
- `GET /settings` returns the full `settings` dataclass as a dict.
- `GET /settings/advanced` returns the advanced subset via `extract_advanced_settings()` from [[Settings Contract]].
- `POST /settings` and `POST /settings/advanced` both delegate to `_update_settings_payload()`. That helper merges only known keys, persists via [[MongoRepository]], and applies side effects:
  - If `mongodb_uri` changed, calls `set_runtime_uri()` and `get_db()` to swap the connection (rolls back on failure).
  - Non-window-state changes trigger `bot_runtime.schedule_tasks()` to rebuild the cron.
  - Sentry-related keys trigger `configure_sentry_runtime(force_reinit=True)`.
  - `schedule_times` changes recompute `next_run` and rewrite `last_run` in MongoDB.

## Depends on
- [[Settings Contract]] — advanced filter
- [[MongoRepository]] — `save_settings`
- [[Bot Entry Point]] — `schedule_tasks`, `configure_sentry_runtime`, `calculate_next_run`

## Used by
- [[Settings Page]] — full form
- [[Window State Dual Storage]] — window keys round-trip

## See also
- [[_index]]
- [[Settings Persistence Flow]]
