---
tags: [operations]
---

# Test Suite

> `uv run --group dev pytest backend/test/` — runs the regression and migration suites under the dev dependency group.

## Source
- `backend/test/test_locator_tracker.py`
- `backend/test/test_migrate_json_to_mongo.py`
- `backend/test/test_local_artifact_maintenance.py`
- `backend/test/test_regressions.py`

## How it works
The `dev` group in `pyproject.toml` adds `pytest` and any test-only deps. The four test modules cover:

- **test_locator_tracker** — dedup keys, throttling, screenshot capture paths.
- **test_migrate_json_to_mongo** — one-shot migration that promotes legacy `output/*.json` into MongoDB collections.
- **test_local_artifact_maintenance** — TTL cleanup of screenshots and DOM snapshots in `output/`.
- **test_regressions** — known-bad scenarios fixed in prior commits.

Run targeted: `uv run --group dev pytest backend/test/test_regressions.py -k draw`.

## Depends on
- [[uv]]

## Used by
- [[LocatorTracker]]
- [[Migrate JSON To Mongo]]

## See also
- [[_index]]
- [[Logging Setup]]
