---
tags: [moc, backend, automation]
---

# Backend / automation — Map of Content

> Playwright page interactions, OpenCV image processing, and selector telemetry.
> These modules are the bridge between the high-level handlers and the live browser.

## Browser interaction

- [[EventNavigator]] — shared page helpers: goto event, close dialogs, authenticate
- [[RetryHelper]] — element polling with state-transition logging
- [[Selectors]] — 50+ centralized CSS selectors for HoYoLab UI
- [[AutoLogin]] — credential-based iframe login fill
- [[RedeemAutofill]] — code paste automation with captcha detection

## Image processing

- [[ImageProcessor]] — OpenCV template matching, ORB feature detection, HTTP pooling

## Telemetry

- [[LocatorTracker]] — selector interaction recorder; per-selector SQLite row
- [[Tracking Helpers]] — `safe_track()` wrapper; never breaks the caller

## See also

- [[_HOME]]
- [[01-Backend/_index|Backend]]
- [[Image Recognition Pipeline]]
- [[Locator Telemetry Pipeline]]
- [[Centralized Selectors Pattern]]
- [[Locator Tracker Instrumentation Pattern]]
