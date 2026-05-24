---
tags: [backend, api]
---

# Locator Tracker Endpoints

> Query, drill into, and clear locator telemetry captured by every instrumented Playwright interaction.

## Source
- `backend/api/routes.py` — primary

## How it works
- `GET /locator-tracker` returns the full deduplicated summary list via `get_all_entries()` — one document per unique selector.
- `GET /locator-tracker/failures` filters to failed selectors only via `get_failure_events()`. Accepts `limit` (1–500) and optional `summary_id` to scope to a single locator's history.
- `GET /locator-tracker/child-scan/{summary_id}` returns the enriched DOM context (`child_scan` array) for a single summary entry via `DataStore.get_locator_child_scan()`.
- `POST /locator-tracker/clear` deletes all telemetry via `clear_entries()` — destructive.

Documents carry references to screenshots stored by [[Screenshot Store]]; the frontend rehydrates thumbnails via [[Asset Endpoints]].

## Depends on
- [[LocatorTracker]] — query / clear helpers
- [[DataStore]] — `get_locator_child_scan` for child scan

## Used by
- [[Locator Tracker Page]] — table, drill-in, clear button

## See also
- [[_index]]
- [[Locator Telemetry Pipeline]]
