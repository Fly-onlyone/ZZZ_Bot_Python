---
tags: [pattern]
---

# Locator Tracker Instrumentation Pattern

> Every Playwright interaction goes through `track_locator()` and always passes the `Locator` object so the tracker can crop an element-level screenshot, not just full-page.

## When to apply
Any new code path that clicks, fills, or reads from a Playwright `Locator`. No exceptions in handlers or the [[EventNavigator]].

## The pattern
```python
loc = page.locator(Selectors.LOGIN_BUTTON)
track_locator(
    page=page,
    selector=Selectors.LOGIN_BUTTON,
    action="click",
    success=True,
    locator=loc,           # MUST pass — enables element-level crop
)
loc.click()
```

Handlers use the local `_safe_track()` wrapper to swallow tracking errors without aborting the run.

## Why
A full-page screenshot at 1920×1080 is hard to read. The tracker uses the `Locator` to compute the element's bounding box and store a focused crop, which makes triage in the [[Locator Tracker Page]] actually useful. Forgetting the kwarg silently degrades to full-page only.

## Don't
- Don't drop the `locator=` kwarg — the tracker falls back to full-page, which is much harder to triage.
- Don't let a tracker exception bubble up — wrap in `_safe_track()`.
- Don't track inside tight loops without throttling — the tracker already throttles success-case screenshots by 1 hour.

## See also
- [[_index]]
- [[LocatorTracker]]
- [[Tracking Helpers]]
- [[Locator Telemetry Pipeline]]
