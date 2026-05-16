---
tags: [glossary]
---

# Locator

> Playwright's lazy selector handle — a reference to one or more DOM elements that resolves at action time, not at creation time.

## How it works
`page.locator(selector)` returns a `Locator` object; the DOM lookup happens when you call `.click()`, `.fill()`, `.is_visible()`, etc. This lets Playwright auto-wait for the element to be ready. In ZZZ Bot the [[Locator Tracker Instrumentation Pattern]] requires you to keep the `Locator` reference around and pass it as the `locator=` kwarg to `track_locator()` so the [[LocatorTracker]] can capture an element-level screenshot crop on failure.

## See also
- [[_index]]
- [[Playwright]]
- [[LocatorTracker]]
