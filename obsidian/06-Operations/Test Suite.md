---
tags: [operations]
---

# Test Suite

> `uv run --group dev pytest backend/test/` — runs the regression and persistence suites under the dev dependency group.

## Source
- `backend/test/conftest.py` — shared fixtures
- `backend/test/test_data_store.py`
- `backend/test/test_locator_tracker.py`
- `backend/test/test_local_artifact_maintenance.py`
- `backend/test/test_regressions.py`

## How it works
The `dev` group in `pyproject.toml` adds `pytest` and any test-only deps. The suites cover:

- **conftest** — shared fixtures, including `sqlite_db`, which spins up a real temp-file SQLite database so persistence tests run against the actual schema.
- **test_data_store** — DataStore CRUD, schema creation, TTL purge, backup export/import, binary-asset round-trips.
- **test_locator_tracker** — dedup keys, throttling, screenshot capture paths.
- **test_local_artifact_maintenance** — local-artifact archiving and cleanup in `output/`.
- **test_regressions** — known-bad scenarios fixed in prior commits.

Run targeted: `uv run --group dev pytest backend/test/test_regressions.py -k draw`.

## Depends on
- [[uv]]

## Used by
- [[DataStore]]
- [[LocatorTracker]]

## See also
- [[_index]]
- [[Logging Setup]]
