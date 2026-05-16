---
tags: [integration]
---

# Playwright

> Browser automation framework that drives the HoYoLab event website; Firefox is bundled into the PyInstaller sidecar so users don't need a system browser.

## Used for
- [[Browser Session Lifecycle]] — persistent context with `storage_state`
- [[Daily Task Cycle]] — all DOM interaction
- [[Manual Login Flow]] — visible window for first-time auth
- [[Locator Telemetry Pipeline]] — every locator interaction is tracked

## Configuration
- Version `playwright==1.55.0` (`pyproject.toml`)
- Browser binaries bundled at `backend/playwright-browsers/` (Firefox), included by `BotSidecar.spec`
- `hide_browser` setting toggles headless / headed mode
- `pytest-playwright==0.7.1` for test fixtures

## Wire-up
- `backend/services/BrowserService.py` — lifecycle (launch, context, close)
- `backend/automation/EventNavigator.py` — navigation primitives
- `backend/automation/LocatorTracker.py` — wraps every `Locator` interaction with telemetry
- `backend/core/ManualLoginManager.py` — opens a visible context for user login

## Auth mode
N/A — manages the user's HoYoLab session cookies via Playwright's storage state.

## Gotchas
- Firefox is preferred because Chromium has been more aggressively fingerprinted on HoYoLab.
- Bundled browser dir must be regenerated when bumping Playwright version.

## See also
- [[_index]]
- [[HoYoLab]]
- [[BrowserService]]
