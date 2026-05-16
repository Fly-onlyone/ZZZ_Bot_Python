---
tags: [backend, core]
---

# GlobalVar

> Module-level runtime singleton that owns `CONFIG` paths, the `AppSettings`/`Account` dataclasses, the FastAPI app, and the staged startup state machine.

## Source

- `backend/core/GlobalVar.py` — primary implementation

## How it works

`is_exe` resolves once at import (also honoring `SIMULATE_EXE=1`). `resource_path()` then branches dev vs exe vs SIMULATE_EXE, with `outside_path=True` directing user data alongside the executable (or under the project root in dev) so it survives updates.

`CONFIG` is built by `generate_config()` from a fixed map of relative paths; only entries flagged as outside-folder (storage, output, screenshot) get `outside_path=True`.

Startup runs in three phases:

```mermaid
stateDiagram-v2
    [*] --> booting
    booting --> warming: initialize_runtime_state()\nloads env, Sentry, Mongo, settings
    warming --> ready: deferred thread\nensures indexes, syncs logs
    booting --> error: bootstrap failed
```

`AppSettings` holds 30+ fields including schedule, hunt polling, Sentry knobs, theme. `Account` holds HoYo and Gmail credentials. Both are `Serializable` dataclasses persisted in MongoDB.

## Depends on

- [[MongoRepository]] — `get_settings`, `get_account`, `save_settings`
- [[Mongo Connection]] — runtime URI switching via `settings.mongodb_uri`
- [[FastAPI]] — `app` instance also serves `/images` and `/screenshot` mounts
- [[Sentry]] — early init when `SENTRY_DSN` is present

## Used by

- [[Bot Entry Point]] — reads `CONFIG`, `settings`, `is_exe`
- Every handler — imports `CONFIG` paths and `settings` flags

## Gotchas

- `SIMULATE_EXE=1` forces exe-style path resolution in dev for testing packaged behavior.
- `settings.mongodb_uri` triggers a live runtime DB switch during `_load_settings`.
- Account loading is lazy via `ensure_accounts_loaded()` to avoid Mongo dependency at import time.

## See also

- [[_index]]
- [[Resource Path Resolution Pattern]]
- [[Settings Persistence Flow]]
