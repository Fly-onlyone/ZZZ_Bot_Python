---
tags: [backend, utils]
---

# Migrate Mongo To SQLite

> One-time copy of an existing local MongoDB database into the embedded SQLite store. Exposed both as a Backup-page button and as a CLI script — both call the same `migrate()` function.

## Source
- `backend/utils/migrate_mongo_to_sqlite.py` — primary

## How it works
`migrate(uri, db_name)` returns a structured report:

```python
{
  "status": "completed" | "no_source",
  "message": str,
  "summary": {"settings": 1, "missions": 3, ...},   # per-collection row counts
  "db_path": "/abs/path/to/zzz_bot.db",
}
```

`pymongo` is imported **lazily** inside `_connect_or_none` so importing this module is cheap and does not require pymongo at import time.

It reads every collection (`settings`, `accounts`, `shopping`, `last_run`, `backup_config`, `missions`, `redemptions`, `app_metadata`, `binary_assets`) and writes the rows into the SQLite database via [[DataStore]] — schema/TTL rules are reused. Ephemeral locator telemetry and the legacy `log_lines` mirror are skipped. BSON `Binary` payloads become SQLite `BLOB`s. Re-running is safe (uses `replace_all_*` / upserts).

## Two callers
- **In-app** — `POST /maintenance/mongo-migration` (see [[Maintenance Endpoints]]). After a `completed` run the endpoint calls `_refresh_runtime_state_after_restore({"settings", "account", "shopping"})` so the migrated settings hot-load without a backend restart.
- **CLI** — `uv run python backend/utils/migrate_mongo_to_sqlite.py [--mongo-uri ...] [--mongo-db ...]`. `main()` calls `migrate()` and pretty-prints the returned report via `_print_report`. Always exits 0 (a `no_source` result is expected, not an error).

## Depends on
- [[DataStore]] — `save_settings`, `save_account`, `save_shopping`, `save_last_run`, `save_backup_config`, `replace_all_missions`, `replace_all_redemptions`, `set_app_metadata_marker`, `upsert_binary_asset`, `ensure_schema`
- `pymongo` — read side; ships in the main runtime dependencies so the in-app button works in the packaged sidecar

## Used by
- `backend/api/routes.py::run_mongo_migration` — Backup-page maintenance card
- CLI users running `migrate_mongo_to_sqlite.py` directly

## Gotchas
- The default URI is `mongodb://localhost:27017`. The endpoint accepts optional `mongo_uri` / `mongo_db` overrides in the request body; the CLI accepts the same flags.
- The default `db_name=None` tries `zzz_bot` then `zzz_bot_dev` from the live MongoDB. A successful match is echoed back in `message`.
- Tests mock `migrate` rather than calling it — the real function needs a live MongoDB to do anything; the route tests in `test_regressions.py` cover both the `completed` and `no_source` branches.

## See also
- [[_index]]
- [[Maintenance Endpoints]]
- [[Data Backup and Restore]]
- [[SQLite]]
- [[Backup Page]]
