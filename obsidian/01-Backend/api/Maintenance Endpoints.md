---
tags: [backend, api]
---

# Maintenance Endpoints

> On-demand legacy JSON import and local artifact cleanup, both invoked from the Tools page.

## Source
- `backend/api/routes.py` — primary

## How it works
- `POST /maintenance/legacy-migration` runs [[Migrate JSON To Mongo]] (`migrate_if_needed(...)`) against `CONFIG["OUTPUT_FOLDER"]`, `STORAGE_PATH`, and `SCREENSHOT_FOLDER`. It then derives which collections were actually rehydrated (`_collect_migrated_collections_from_report`) and calls `_refresh_runtime_state_after_restore()` so live `settings`/`accounts` singletons and the scheduler pick up the new data. Response status is `completed` or `completed_with_warnings` depending on partial / invalid artifacts.
- `POST /maintenance/local-cleanup` calls `cleanup_local_artifacts_once(...)` from `utils/local_artifact_maintenance.py`, returning a structured cleanup report. Used to prune legacy files now that MongoDB is authoritative.

Both endpoints open Sentry spans so cleanup work is traced.

## Depends on
- [[Migrate JSON To Mongo]] — migration logic
- [[MongoRepository]] — runtime state refresh
- [[Sentry]] — span tracing

## Used by
- [[Tools Page]] — manual buttons

## See also
- [[_index]]
- [[Data Backup and Restore]]
