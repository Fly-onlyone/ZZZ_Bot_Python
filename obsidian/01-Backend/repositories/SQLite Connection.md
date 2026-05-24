---
tags: [backend, repositories]
---

# SQLite Connection

> Shared embedded-SQLite connection manager: one `sqlite3.Connection` for the whole process, guarded by a single `RLock` because the backend is multi-threaded.

## Source
- `backend/repositories/connection.py` — primary

## How it works
1. `get_runtime_mode()` returns `"exe"` when `SIMULATE_EXE=1` or `sys.frozen`, else `"dev"`.
2. `get_db_path()` resolves the database file under `data/`: `zzz_bot_dev.db` in dev, `zzz_bot.db` in the packaged exe. The directory and file are created on first launch.
3. `get_connection()` lazily opens one shared `sqlite3.Connection` with `check_same_thread=False` and WAL journal mode, then reuses it for every call.
4. `get_lock()` returns the process-wide `threading.RLock` — callers must hold it around every read/write since the connection is shared across threads.
5. `reset_connection()` closes and drops the cached connection (used by tests and after a backup restore); `get_connection_debug_info()` reports the resolved path and runtime mode for diagnostics.

## Depends on
- [[SQLite]] — the embedded database file
- [[SIMULATE_EXE Switch]] — toggles runtime mode without packaging

## Used by
- [[DataStore]] — every CRUD call funnels through `get_connection()` + `get_lock()`
- [[System Endpoints]] — exposes `get_connection_debug_info()`

## Gotchas
- There is **one** connection for the whole process — never open your own; always go through `get_connection()` and hold `get_lock()`.
- Dev and exe modes use **different database file names** so dev data never overwrites packaged data.
- No connection URI, no credentials, no env vars — the old `MONGODB_URI*` resolution and runtime-reconnect logic are gone.

## See also
- [[_index]]
- [[DataStore]]
- [[Port Configuration]]
