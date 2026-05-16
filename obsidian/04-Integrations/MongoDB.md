---
tags: [integration]
---

# MongoDB

> Primary persistence layer for the backend: settings, account, shopping, mission reports, redemptions, and locator telemetry — all live in MongoDB collections.

## Used for
- [[Settings Persistence Flow]] — `settings` collection
- Mission reports — `missions` collection (one doc per run)
- Locator telemetry — `locator_tracker` collection with 7-day TTL index
- Redemption history — `redemptions` collection
- [[Data Backup and Restore]] — export/import of all collections

## Configuration
- `pymongo>=4.0` (`pyproject.toml`)
- Connection URI configured in backend settings (see [[Mongo Connection]])
- Single-doc collections: `settings`, `account`, `shopping`
- Multi-doc collections: `missions`, `redemptions`, `locator_tracker`

## Wire-up
- `backend/repositories/MongoRepository.py` — CRUD + export/import
- `backend/repositories/Mongo Connection.py` (mongo connection wiring)
- `backend/repositories/DataRepository.py` — abstraction over MongoDB + JSON fallback

## Auth mode
Connection string (URI with optional username/password) configured via UI.

## Gotchas
- New collections must be registered in `_SINGLE_DOC_COLLECTIONS` or `_MULTI_DOC_COLLECTIONS` in `MongoRepository.py` — otherwise they're silently excluded from backup export/import.
- `locator_tracker` has a 7-day TTL index — old documents disappear automatically.

## See also
- [[_index]]
- [[MongoRepository]]
- [[Backup Endpoints]]
