---
tags: [backend, repositories]
---

# DataRepository

> Generic `IRepository[T]` abstraction plus legacy JSON-file implementations for settings and shopping data.

## Source
- `backend/repositories/DataRepository.py` — primary

## How it works
1. `IRepository[T]` — abstract base with `get_by_id`, `get_all`, `save`, `delete`, `exists`.
2. `JsonFileRepository` — concrete implementation that reads/writes `{id}.json` files inside a configured directory; dataclasses are converted via `asdict`; `get_or_create()` seeds defaults on first read.
3. `SettingsRepository` — subclass with `get_settings()` factory (default schedule times, hunt-mode flags, theme) and an `update_settings()` patcher.
4. `ShoppingRepository` — subclass with `get_shopping_data()`, `update_selected_items()`, `update_hunt_items()`.

The class lattice predates the move to Mongo and is preserved for test fixtures and migration tooling.

## Depends on
- *(stdlib only — json, pathlib, dataclasses)*

## Used by
- [[Migrate JSON To Mongo]] — reads legacy JSON before insertion
- *(legacy tests and migration scripts)*

## Gotchas
- **Deprecated for runtime persistence** — all live reads/writes go through [[MongoRepository]]; do not introduce new callers.

## See also
- [[_index]]
- [[MongoRepository]]
- [[Serializable Data Pattern]]
