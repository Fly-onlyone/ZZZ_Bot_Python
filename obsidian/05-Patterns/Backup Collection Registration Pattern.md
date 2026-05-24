---
tags: [pattern]
---

# Backup Collection Registration Pattern

> Every persisted collection must be registered in `_SINGLE_DOC_COLLECTIONS` or `_MULTI_DOC_COLLECTIONS` in `DataStore.py` — otherwise it won't be backed up or restored.

## When to apply
Whenever you create a new persisted collection (a new `documents` collection name or a new dedicated table). Do it in the same commit that introduces the collection.

## The pattern
```python
# backend/repositories/DataStore.py

# One canonical row in the documents table (settings, account, shopping, …)
_SINGLE_DOC_COLLECTIONS = {"settings", "account", "shopping"}

# Dedicated tables holding many rows (missions, redemptions, locator_tracker, your_new_one)
_MULTI_DOC_COLLECTIONS = {"missions", "redemptions", "locator_tracker"}
```

Pick `_SINGLE_DOC_COLLECTIONS` when there's exactly one document (configuration-like, lives in the generic `documents` table); `_MULTI_DOC_COLLECTIONS` when there are many rows (log-like, usually a dedicated table).

## Why
`export_all_data()` and `import_data()` iterate these sets to know what to dump. An unregistered collection is invisible to `/backup/export` and silently dropped on `/backup/import` — users lose data without warning.

## Don't
- Don't add the collection to both sets — pick one.
- Don't rely on dynamic discovery (querying `sqlite_master`) — the explicit set is the contract.
- Don't forget the [[Backup Page]] summary lists these sets, so unregistered collections also vanish from the UI.
- Don't forget that if the new collection has retention, you also need an `expires_at` column and an entry in `purge_expired()` — SQLite has no automatic TTL.

## See also
- [[_index]]
- [[DataStore]]
- [[Backup Endpoints]]
- [[Data Backup and Restore]]
