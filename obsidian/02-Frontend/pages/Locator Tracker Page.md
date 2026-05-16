---
tags: [frontend, pages]
---

# Locator Tracker Page

> Inspector table for Playwright selector telemetry with page/element screenshots, failure history, and child-scan gallery.

## How it works
Fetches `locator-tracker` summaries via [[DataLoader]] (1 min `gcTime`) and renders a sortable table with handler filter, failures-only toggle, hit count, last error, and relative `last_seen`. Pagination is 25 rows per page.

Clicking a row expands a `DetailPanel` that lazily queries `locator-tracker/failures` and `locator-tracker/child-scan/{id}` — surfacing the latest 50 failure events plus a thumbnail grid of sibling element screenshots (preview 24, expandable). Screenshots open in a `Dialog`; DOM snapshots open in a new tab. **Clear All** invokes [[Locator Tracker Endpoints]] `clear` mutation.

## Source
- `frontend/src/pages/LocatorTracker.jsx` — primary

## Depends on
- [[Locator Tracker Endpoints]] — summary / failures / child-scan / clear
- [[DataLoader]] — query + action mutation
- [[Asset Endpoints]] — `/assets/screenshot/{file}`

## Used by
- [[Tools Page]] — Locator tab

## See also
- [[_index]]
- [[Locator Telemetry Pipeline]]
- [[LocatorTracker]]
