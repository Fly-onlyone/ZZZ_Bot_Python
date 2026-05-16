---
tags: [pattern]
---

# Backup Collection Registration Pattern

> Every MongoDB collection must be registered in `_SINGLE_DOC_COLLECTIONS` or `_MULTI_DOC_COLLECTIONS` in `MongoRepository.py` — otherwise it won't be backed up or restored.

## When to apply
Whenever you create a new MongoDB collection. Do it in the same commit that introduces the collection.

## The pattern
```python
# backend/repositories/MongoRepository.py

# One canonical doc per collection (settings, account, shopping)
_SINGLE_DOC_COLLECTIONS = {"settings", "account", "shopping"}

# Array-of-docs collections (missions, redemptions, locator_tracker, your_new_one)
_MULTI_DOC_COLLECTIONS = {"missions", "redemptions", "locator_tracker"}
```

Pick `_SINGLE_DOC_COLLECTIONS` when there's exactly one document (configuration-like); `_MULTI_DOC_COLLECTIONS` when there are many documents (log-like).

## Why
`export_data()` and `import_data()` iterate these sets to know what to dump. An unregistered collection is invisible to `/backup/export` and silently dropped on `/backup/import` — users lose data without warning.

## Don't
- Don't add the collection to both sets — pick one.
- Don't rely on dynamic discovery (`db.list_collection_names()`) — the explicit set is the contract.
- Don't forget the [[Backup Page]] summary lists these sets, so unregistered collections also vanish from the UI.

## See also
- [[_index]]
- [[MongoRepository]]
- [[Backup Endpoints]]
- [[Data Backup and Restore]]
