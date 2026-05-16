---
tags: [backend, automation]
---

# Tracking Helpers

> Thin, exception-swallowing wrappers that route handler-side locator events to [[LocatorTracker]] without breaking automation.

## Source
- `backend/automation/tracking.py` — primary

## How it works
1. `extract_selector(locator)` peeks `locator._impl_obj._selector`, falling back to parsing `repr(locator)` with a precompiled regex when the private attribute is missing. Returns `"unknown"` if everything fails.
2. `safe_track(page, selector, handler, action, success, ...)` calls `LocatorTracker.track_locator` inside `with suppress(Exception)` so a telemetry hiccup can never abort the surrounding handler.
3. `safe_track_locator(locator, ...)` is the locator-only convenience overload; it derives both the page and selector before delegating to `safe_track`.

These helpers are the canonical entry points used across every handler — direct calls to `track_locator` are avoided so the swallowing contract is guaranteed.

## Depends on
- [[LocatorTracker]] — lazy import inside `safe_track`
- [[Playwright]] — `Locator` and `Page` types

## Used by
- [[EventNavigator]] — visibility checks
- [[RetryHelper]] — wait/count outcomes
- [[MissionHandler]], [[ShoppingHandler]], [[DrawHandler]], [[HuntModeHandler]]
- [[ImageProcessor]] — lottery logo telemetry

## Gotchas
- Never raises by design — failing telemetry is invisible to handlers; check the logger if you suspect drops.

## See also
- [[_index]]
- [[Locator Tracker Instrumentation Pattern]]
- [[LocatorTracker]]
