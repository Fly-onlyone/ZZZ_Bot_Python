---
tags: [integration]
---

# SQLite

> Primary persistence layer for the backend: settings, account, shopping, mission reports, redemptions, locator telemetry, and binary assets — all live in a single embedded SQLite database file.

## Used for
- [[Settings Persistence Flow]] — `documents` table, `collection='settings'`
- Mission reports — `missions` table (one row per run, 5-day retention)
- Locator telemetry — `locator_tracker` + `locator_tracker_failures` tables (7-day retention)
- Redemption history — `redemptions` table (30-day retention)
- Binary assets — `binary_assets` table (screenshots, storage state)
- [[Data Backup and Restore]] — export/import of all tables

## Configuration
- `sqlite3` from the Python stdlib — no external server, no driver dependency
- Database file lives under `data/`: `zzz_bot_dev.db` in dev, `zzz_bot.db` in the packaged exe — created automatically on first launch (see [[SQLite Connection]])
- No connection URI, no credentials — the file path is the only configuration
- WAL journal mode, `check_same_thread=False`, one shared connection guarded by a process-wide `RLock`

## Schema
- `documents(collection, doc_id, data, updated_at)` — generic key-value table holding the single-doc collections: `settings`, `account`, `shopping`, `last_run`, `backup_config`
- Dedicated tables: `missions`, `redemptions`, `locator_tracker`, `locator_tracker_failures`, `binary_assets`, `app_metadata`
- JSON payloads are stored as `TEXT`; binary payloads as `BLOB` (replacing the BSON `Binary` type)
- TTL tables (`missions`, `redemptions`, `locator_tracker`, `locator_tracker_failures`, `binary_assets`) carry an `expires_at` column

## Wire-up
- `backend/repositories/DataStore.py` — CRUD + export/import + schema + purge
- `backend/repositories/connection.py` — shared connection + lock (see [[SQLite Connection]])
- `backend/repositories/DataRepository.py` — legacy JSON abstraction kept for migration tooling only

## Gotchas
- SQLite has **no automatic TTL**. Unlike MongoDB's `TTLMonitor`, expiry is application-driven: `purge_expired()` runs once at startup (inside `ensure_schema()`) and, throttled to once per 60s, before reads of TTL tables. Any new TTL table must be added to `purge_expired()` or its rows live forever.
- New collections must be registered in `_SINGLE_DOC_COLLECTIONS` or `_MULTI_DOC_COLLECTIONS` in `DataStore.py` — otherwise they're silently excluded from backup export/import. See [[Backup Collection Registration Pattern]].
- The backend is multi-threaded; every read/write must hold `get_lock()` because the single connection is shared.

## See also
- [[_index]]
- [[DataStore]]
- [[SQLite Connection]]
- [[Backup Endpoints]]
- [[TTL]]
