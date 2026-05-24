---
tags: [architecture, flow]
---

# Locator Telemetry Pipeline

> Every Playwright locator interaction is wrapped in `safe_track()`, which records
> selector + outcome + screenshots to the embedded SQLite store. The frontend reads
> from `/locator-tracker` to surface broken selectors before the user notices.

## Source

- `backend/automation/LocatorTracker.py` — recorder + dedup
- `backend/automation/tracking.py` — `safe_track()` wrapper
- `backend/utils/screenshot_store.py` — binary asset persistence
- `frontend/src/pages/LocatorTracker.jsx` — UI

## How it works

```mermaid
flowchart LR
    H[Handler op] --> SW[safe_track wrap]
    SW --> OP[locator.click/fill/etc]
    OP -->|success| TS[throttled element screenshot]
    OP -->|failure| FS[full-page + element + DOM snapshot]
    TS --> DK[locator_tracker table upsert]
    FS --> DK
    DK -->|expires_at 7d| EX[purge_expired]
    DK --> API[/locator-tracker endpoints]
    API --> FE[Locator Tracker Page]
```

Dedup key is `locator:<md5(selector)[:12]>` — one row per unique selector. On
success, screenshots are throttled to once per hour to avoid spamming the
`binary_assets` table. On failure, every detail is captured (page screenshot,
element crop, DOM snapshot as a `BLOB`). See [[Locator Tracker Instrumentation Pattern]]
for the discipline contributors must follow when adding new locator calls.

## Depends on

- [[LocatorTracker]] — the recorder
- [[Tracking Helpers]] — never-raising wrapper
- [[Screenshot Store]] — binary asset persistence
- [[SQLite]] — `locator_tracker` table with `expires_at` retention
- [[Locator Tracker Endpoints]] — read path

## Used by

- [[EventNavigator]], [[RetryHelper]], [[MissionHandler]], [[ShoppingHandler]], [[DrawHandler]], [[HuntModeHandler]] — every instrumented module
- [[Locator Tracker Page]] — frontend display
- [[Locator Tracker Instrumentation Pattern]] — discipline

## Gotchas

- Always pass `locator=` kwarg when a `Locator` object is in scope — without it, the tracker can't capture the element-level crop, only the full page.
- Retention is 7 days; older failures are gone forever. If a flake recurs monthly, it'll look brand new each time. Expiry is not automatic — `purge_expired()` (see [[DataStore]]) deletes stale rows at startup and before reads.

## See also

- [[_index]]
- [[Locator Tracker Instrumentation Pattern]]
- [[LocatorTracker]]
- [[Locator Tracker Page]]
