---
tags: [backend, api]
---

# Maintenance Endpoints

> On-demand maintenance actions, invoked from the Backup page's Maintenance section.

## Source
- `backend/api/routes.py` — primary

## How it works
- `POST /maintenance/local-cleanup` — calls `cleanup_local_artifacts_once(...)` from
  `utils/local_artifact_maintenance.py`, returning a structured cleanup report. It archives
  stale local artifacts (logs, screenshots, DOM snapshots) into a ZIP and deletes the
  originals, since SQLite is the authoritative store.
- `POST /maintenance/mongo-migration` — calls `migrate(uri, db_name)` from
  [[Migrate Mongo To SQLite]] and returns the structured report (`status`, `message`,
  `summary`, `db_path`). Accepts optional `mongo_uri` / `mongo_db` in the JSON body;
  defaults are `mongodb://localhost:27017` and "try `zzz_bot` then `zzz_bot_dev`". When
  `status == "completed"` the endpoint also calls `_refresh_runtime_state_after_restore({"settings", "account", "shopping"})`
  so the migrated documents hot-load into the running app without a backend restart;
  any refresh warnings are merged into `report["errors"]`.

Both endpoints open a Sentry span so the work is traced.

> The former `POST /maintenance/legacy-migration` endpoint (which imported old JSON files
> into MongoDB) is permanently removed.

## Depends on
- `utils/local_artifact_maintenance.py` — cleanup logic
- [[Migrate Mongo To SQLite]] — migration function (returns a dict report)
- `_refresh_runtime_state_after_restore` (same module) — hot-loads restored settings /
  account / shopping into the running app
- [[Sentry]] — span tracing

## Used by
- [[Backup Page]] — Maintenance section cards ("Migrate from MongoDB", "Local Cleanup")

## See also
- [[_index]]
- [[Data Backup and Restore]]
