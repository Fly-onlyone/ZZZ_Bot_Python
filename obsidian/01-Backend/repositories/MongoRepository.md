---
tags: [backend, repositories]
---

# MongoRepository

> Single runtime persistence backend for ZZZ Bot — settings, account, shopping, missions, redemptions, locator telemetry, and backup/restore.

## Source
- `backend/repositories/MongoRepository.py` — primary

## How it works
Module-level functions wrap a `get_db()` connection:

- **Single-doc collections** (`settings`, `account`, `shopping`, `last_run`) — upserted with `find_one_and_replace({"_id": "default"}, …, upsert=True)`.
- **Multi-doc collections** — `missions` (5-day TTL), `redemptions` (30-day TTL), `locator_tracker` + `locator_tracker_failures` (7-day TTL), `app_metadata` markers.
- **Backup** — `export_all_data()` aggregates every collection into one document; `import_data(data, collections)` selectively restores using saver dispatch tables. Ephemeral collections are skipped on restore.
- **Indexes** — `_ensure_indexes()` is idempotent per `(client_id, db_name)`; bumping `LOCATOR_TRACKER_SCHEMA_MARKER` wipes diagnostics once.

## Depends on
- [[Mongo Connection]] — `get_db()` factory
- [[MongoDB]] — TTL indexes, `find_one_and_replace`

## Used by
- [[Settings Endpoints]], [[Shopping Endpoints]], [[Account Endpoints]], [[Mission Endpoints]], [[Backup Endpoints]]
- [[LocatorTracker]] — upserts and failure events
- [[MissionHandler]], [[ShoppingHandler]], [[DrawHandler]] — read/write per-task data

## Gotchas
- JSON file repo path is **legacy/deprecated** — Mongo is the single runtime backend.
- When adding a new collection, register it in `_SINGLE_DOC_COLLECTIONS` or `_MULTI_DOC_COLLECTIONS` and add a saver/getter; see [[Backup Collection Registration Pattern]].

## See also
- [[_index]]
- [[Data Backup and Restore]]
- [[Mongo Connection]]
