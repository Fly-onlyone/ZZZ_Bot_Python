---
tags: [backend, repositories]
---

# DataStore

> Single runtime persistence backend for ZZZ Bot — settings, account, shopping, missions, redemptions, locator telemetry, binary assets, and backup/restore. A flat module of functions over an embedded SQLite database.

## Source
- `backend/repositories/DataStore.py` — primary

## How it works
Module-level functions wrap the shared `get_connection()` / `get_lock()` pair from [[SQLite Connection]]:

- **Single-doc collections** (`settings`, `account`, `shopping`, `last_run`, `backup_config`) — stored as rows in the generic `documents(collection, doc_id, data, updated_at)` table; upserted with `INSERT … ON CONFLICT(collection, doc_id) DO UPDATE`. JSON payloads serialized to the `data` TEXT column.
- **Dedicated tables** — `missions` (5-day retention), `redemptions` (30-day retention), `locator_tracker` + `locator_tracker_failures` (7-day retention), `binary_assets`, `app_metadata` markers. TTL tables carry an `expires_at` column.
- **Schema** — `ensure_schema()` creates every table idempotently and runs `purge_expired()` once at startup. An `ensure_indexes` alias is kept for call-site compatibility.
- **TTL purge** — `purge_expired()` deletes rows whose `expires_at` has passed. SQLite has no `TTLMonitor`, so this is called at startup and, throttled to once per 60s, before reads of TTL tables.
- **Backup** — `export_all_data()` aggregates every collection into one envelope; `import_data(data, collections)` selectively restores using saver dispatch tables. Ephemeral collections are skipped on restore. `get_data_summary()` reports row counts.
- **Binary assets** — `upsert_binary_asset()` / `get_binary_asset()` / `get_latest_binary_asset()` / `delete_binary_asset()` store BLOB payloads in `binary_assets` (replacing the old BSON `Binary` documents).

Public function names and signatures are unchanged from the former `MongoRepository`: `get_settings`, `save_settings`, `get_account`, `save_account`, `get_shopping`, `save_shopping`, `get_missions`, `get_today_mission`, `save_mission_day`, `replace_all_missions`, `get_redemptions`, `save_redemption`, `update_redemption`, `replace_all_redemptions`, `get_last_run`, `save_last_run`, `upsert_locator_entry`, `get_locator_entries`, `get_locator_entry`, `get_locator_child_scan`, `save_locator_failure_event`, `get_locator_failure_events`, `clear_locator_entries`, `export_all_data`, `import_data`, `get_data_summary`, `get_backup_config`, `save_backup_config`, `has_app_metadata_marker`, `set_app_metadata_marker`. `repair_redemptions_indexed_at_once()` is now a no-op stub.

## Depends on
- [[SQLite Connection]] — `get_connection()`, `get_lock()`
- [[SQLite]] — schema design, `expires_at` retention columns

## Used by
- [[Settings Endpoints]], [[Shopping Endpoints]], [[Account Endpoints]], [[Mission Endpoints]], [[Backup Endpoints]]
- [[LocatorTracker]] — upserts and failure events
- [[Screenshot Store]], [[Storage State Store]] — binary-asset reads/writes
- [[MissionHandler]], [[ShoppingHandler]], [[DrawHandler]] — read/write per-task data

## Gotchas
- JSON file repo path is **legacy/deprecated** — SQLite is the single runtime backend.
- When adding a new collection, register it in `_SINGLE_DOC_COLLECTIONS` or `_MULTI_DOC_COLLECTIONS` and add a saver/getter; see [[Backup Collection Registration Pattern]].
- When adding a new TTL table, also add it to `purge_expired()` — SQLite has no automatic expiry.
- Every read/write must run under `get_lock()`; the single connection is shared across the backend's threads.

## See also
- [[_index]]
- [[Data Backup and Restore]]
- [[SQLite Connection]]
