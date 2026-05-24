---
tags: [backend, api]
---

# Settings Endpoints

> Read and update the shared settings document, with side effects on schedulers and the Sentry runtime.

## Source
- `backend/api/routes.py` — primary

## How it works
- `GET /settings` returns the full `settings` dataclass as a dict.
- `GET /settings/advanced` returns the advanced subset via `extract_advanced_settings()` from [[Settings Contract]].
- `POST /settings` and `POST /settings/advanced` both delegate to `_update_settings_payload()`. That helper merges only known keys, persists via [[DataStore]], and applies side effects:
  - Non-window-state changes trigger `bot_runtime.schedule_tasks()` to rebuild the cron.
  - Sentry-related keys trigger `configure_sentry_runtime(force_reinit=True)`.
  - `schedule_times` changes recompute `next_run` and rewrite `last_run` in SQLite.

There is no database-connection side effect — the embedded SQLite file has no URI, and the former `mongodb_uri` setting field has been removed.

## Depends on
- [[Settings Contract]] — advanced filter
- [[DataStore]] — `save_settings`
- [[Bot Entry Point]] — `schedule_tasks`, `configure_sentry_runtime`, `calculate_next_run`

## Used by
- [[Settings Page]] — full form
- [[Window State Dual Storage]] — window keys round-trip

## See also
- [[_index]]
- [[Settings Persistence Flow]]
