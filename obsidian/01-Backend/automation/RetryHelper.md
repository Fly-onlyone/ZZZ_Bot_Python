---
tags: [backend, automation]
---

# RetryHelper

> Polling utilities for clicking until a screen appears, counting until non-zero, and waiting on locator states.

## Source
- `backend/automation/RetryHelper.py` — primary

## How it works
Three primitives implement the [[Retry Polling Pattern]]:

1. `retry_until_screen_appears(screen, button, max_retries=10, delay_ms=1000)` — repeatedly clicks `button` and checks `screen.is_visible`; on exhaustion saves a diagnostic page screenshot, dumps the first 10 image tags, and emits a `safe_track_locator` failure.
2. `retry_until_non_zero_count(locator)` — polls `locator.count()`; tracks success/failure.
3. `wait_for_element(locator, state="visible", timeout=5000)` — typed wrapper around `locator.wait_for` that always logs and reports to [[LocatorTracker]].

Defaults: 10 retries, 1000 ms delay, 5000 ms visibility timeout.

## Depends on
- [[Playwright]] — locator and timeout error types
- [[Tracking Helpers]] — emits failure/success telemetry
- [[Screenshot Store]] — diagnostic dump on exhausted retries

## Used by
- [[ImageProcessor]] — `retry_until_non_zero_count` while finding avatars
- [[MissionHandler]], [[ShoppingHandler]], [[HuntModeHandler]], [[RedeemAutofill]]

## Gotchas
- The diagnostic image dump in `retry_until_screen_appears` is best-effort — wrapped in try/except so a failed inspector never masks the real timeout.

## See also
- [[_index]]
- [[Retry Polling Pattern]]
- [[LocatorTracker]]
