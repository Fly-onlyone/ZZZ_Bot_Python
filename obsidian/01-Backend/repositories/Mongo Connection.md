---
tags: [backend, repositories]
---

# Mongo Connection

> Lazy `MongoClient` factory that resolves URI from runtime override, env var, or runtime-mode default.

## Source
- `backend/repositories/connection.py` — primary

## How it works
1. `get_runtime_mode()` returns `"exe"` when `SIMULATE_EXE=1` or `sys.frozen`, else `"dev"`.
2. `get_effective_mongodb_uri()` resolves in order: runtime override (set from settings UI) → `MONGODB_URI_DEV`/`MONGODB_URI_EXE` env → generic `MONGODB_URI` → built-in default (`zzz_bot_dev` / `zzz_bot`).
3. `get_db()` lazily creates `MongoClient(uri, serverSelectionTimeoutMS=5000)`, runs `admin ping` to verify reachability, then `client.get_default_database()` (fallback to mode-specific name).
4. `set_runtime_uri()` swaps the override and `reset_connection()` to force reconnection on next call; `get_connection_debug_info()` reports masked URI and source for diagnostics.

## Depends on
- [[MongoDB]] — server reachability
- [[SIMULATE_EXE Switch]] — toggles runtime mode without packaging

## Used by
- [[MongoRepository]] — every CRUD call funnels through `get_db()`
- [[System Endpoints]] — exposes `get_connection_debug_info()`
- [[Settings Endpoints]] — can update runtime URI

## Gotchas
- Credentials in the URI are stripped only by `_masked_uri()` — never log the raw URI directly.
- Dev and exe modes use **different default database names** so dev data never overwrites packaged data.

## See also
- [[_index]]
- [[MongoRepository]]
- [[Port Configuration]]
