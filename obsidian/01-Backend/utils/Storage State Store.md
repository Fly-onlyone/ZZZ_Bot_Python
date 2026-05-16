---
tags: [backend, utils]
---

# Storage State Store

> Mongo-first persistence for Playwright `storage_state` (cookies + localStorage), with optional local file backup and a context-options builder.

## Source
- `backend/utils/storage_state_store.py` — primary

## How it works
Storage-state JSON is held in the `binary_assets` collection under id `storage_state:<filename>` and category `storage_state`. Payloads are encoded UTF-8 JSON wrapped in `bson.Binary`.

- `load_storage_state(storage_path)` — first looks up the asset by id derived from `storage_path`; on miss falls back to the most recent `storage_state` asset (sorted by `updated_at`). Decodes UTF-8 and `json.loads`. Returns dict or `None`. Wrapped in a Sentry span.
- `build_context_options(storage_path)` — used by [[BrowserService]] to build the Playwright `new_context()` kwargs. Mongo wins; on miss it falls back to the local `storage_path` file if present; otherwise returns `{}` (no session).
- `save_storage_state(storage_path, storage_state, write_local_backup=True)` — upserts the asset and optionally writes a local JSON backup so a Mongo outage doesn't strand authentication.
- `save_context_storage_state(context, ...)` — calls `context.storage_state()` and persists the result. Used after [[Manual Login Flow]] completes.

## Depends on
- [[Mongo Connection]] — `binary_assets`
- [[Playwright]] — `context.storage_state()`
- [[Sentry]] — span tracing

## Used by
- [[BrowserService]] — context bootstrap
- [[ManualLoginManager]] — save after successful login

## See also
- [[_index]]
- [[Browser Session Lifecycle]]
