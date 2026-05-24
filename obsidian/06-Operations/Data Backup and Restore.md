---
tags: [operations]
---

# Data Backup and Restore

> The `/backup/export` and `/backup/import` endpoints serialize the SQLite tables to a single JSON file and back; the [[Backup Page]] drives this with table-level checkboxes.

## Source
- `backend/repositories/DataStore.py` — `export_all_data()`, `import_data()`
- `backend/api/routes.py` — `/backup/*` endpoints
- `frontend/src/pages/BackupPage.jsx`

## How it works
Export reads every collection listed in `_SINGLE_DOC_COLLECTIONS` (one canonical row in the `documents` table) and `_MULTI_DOC_COLLECTIONS` (dedicated tables holding many rows) and emits a versioned JSON envelope. Import accepts that envelope, validates the schema, then upserts per the same sets. `/backup/summary` reports row counts so the UI can show a before/after preview, and `/backup/browse` lets the user peek inside a backup file before restoring.

Adding a new collection requires registering it via the [[Backup Collection Registration Pattern]] — otherwise it's silently skipped by both export and import.

## Depends on
- [[DataStore]]
- [[Backup Endpoints]]
- [[Backup Collection Registration Pattern]]

## Used by
- [[Backup Page]]

## Gotchas
- Unregistered collections vanish from export, the UI summary, and import — fail silently.
- The backup envelope is plain JSON; binary-asset `BLOB`s are base64-encoded inside it.

## See also
- [[_index]]
- [[Output Files]]
- [[SQLite]]
