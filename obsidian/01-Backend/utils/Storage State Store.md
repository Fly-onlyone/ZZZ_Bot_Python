---
tags: [backend, utils]
---

# Storage State Store

> SQLite-first persistence for Playwright `storage_state` (cookies + localStorage), with optional local file backup and a context-options builder.

## Source
- `backend/utils/storage_state_store.py` — primary

## How it works
Storage-state JSON is held in the `binary_assets` table under id `storage_state:<filename>` and category `storage_state`. Payloads are UTF-8 JSON stored as a SQLite `BLOB`. The store no longer touches the database directly — all reads/writes go through [[DataStore]]'s binary-asset functions.

- `load_storage_state(storage_path)` — looks up the asset via `DataStore.get_binary_asset` by id derived from `storage_path`; on miss falls back to `DataStore.get_latest_binary_asset` for the `storage_state` category. Decodes UTF-8 and `json.loads`. Returns dict or `None`. Wrapped in a Sentry span.
- `build_context_options(storage_path)` — used by [[BrowserService]] to build the Playwright `new_context()` kwargs. SQLite wins; on miss it falls back to the local `storage_path` file if present; otherwise returns `{}` (no session).
- `save_storage_state(storage_path, storage_state, write_local_backup=True)` — calls `DataStore.upsert_binary_asset` and optionally writes a local JSON backup so a database problem doesn't strand authentication.
- `save_context_storage_state(context, ...)` — calls `context.storage_state()` and persists the result. Used after [[Manual Login Flow]] completes.

## Depends on
- [[DataStore]] — `upsert_binary_asset`, `get_binary_asset`, `get_latest_binary_asset`
- [[Playwright]] — `context.storage_state()`
- [[Sentry]] — span tracing

## Used by
- [[BrowserService]] — context bootstrap
- [[ManualLoginManager]] — save after successful login

## See also
- [[_index]]
- [[Browser Session Lifecycle]]
