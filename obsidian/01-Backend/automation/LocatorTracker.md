---
tags: [backend, automation]
---

# LocatorTracker

> Per-selector telemetry that captures screenshots, DOM snapshots, and rolling failure events for every Playwright interaction.

## Source
- `backend/automation/LocatorTracker.py` — primary

## How it works
```mermaid
flowchart TD
    A[track_locator call] --> B[hash selector md5 trim 12]
    B --> C[summary id locator:handler:action:hash]
    C --> D{success?}
    D -- failure --> E[capture mode failure if 15 min cooldown elapsed]
    D -- success after prior failure --> F[capture mode recovery]
    D -- success --> G[skip capture]
    E --> H[full-page PNG + DOM HTML + child scan]
    F --> H
    H --> I[upsert summary doc]
    H --> J[insert failure event row]
```

Summary rows live in the `locator_tracker` table (7-day retention via `expires_at`); failure events live in `locator_tracker_failures`. Element-level crops are saved when the `Locator` argument is visible; the JS-driven child scan crops up to six visible boxes from the full-page screenshot.

## Depends on
- [[DataStore]] — `upsert_locator_entry`, `save_locator_failure_event`, `get_locator_child_scan`
- [[Screenshot Store]] — binary asset persistence with retention metadata
- [[Playwright]] — locator + page APIs

## Used by
- [[Tracking Helpers]] — `safe_track` wrapper
- [[EventNavigator]], [[RetryHelper]], [[MissionHandler]], [[ShoppingHandler]], [[DrawHandler]], [[HuntModeHandler]]
- [[Locator Tracker Endpoints]] — read/clear API

## Gotchas
- `_FAILURE_CAPTURE_COOLDOWN_SECONDS = 15 * 60` throttles redundant artefact saves per summary id.
- Bumping `LOCATOR_TRACKER_SCHEMA_MARKER` wipes existing diagnostics on next start (tracked in the `app_metadata` table).
- 7-day retention is not automatic — `purge_expired()` deletes stale `locator_tracker` / `locator_tracker_failures` rows at startup and before reads.

## See also
- [[_index]]
- [[Locator Telemetry Pipeline]]
- [[Locator Tracker Instrumentation Pattern]]
