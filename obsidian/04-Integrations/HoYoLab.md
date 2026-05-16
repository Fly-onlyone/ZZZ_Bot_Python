---
tags: [integration]
---

# HoYoLab

> HoYoverse community event website — the target surface for every automation flow in this project (daily missions, shopping, prize draws, code redemption).

## Used for
- [[Daily Task Cycle]] — check-in, mission claims
- [[Hunt Mode Lifecycle]] — timed shop renewal purchases
- [[Browser Session Lifecycle]] — persistent login storage

## Configuration
- Login credentials are not stored; a persistent Playwright `storage_state` lives under `authentication data/` (managed by [[Storage State Store]])
- First-time auth via the [[Manual Login Page]] in the desktop UI
- Redeem codes posted through HoYoLab's gift redemption flow (handled by [[RedeemAutofill]])

## Wire-up
- `backend/automation/EventNavigator.py` — navigates between event pages
- `backend/automation/Selectors.py` — centralized CSS selectors for HoYoLab DOM
- `backend/automation/RedeemAutofill.py` — gift code redemption
- `backend/handlers/MissionHandler.py`, `ShoppingHandler.py`, `DrawHandler.py`, `HuntModeHandler.py` — task orchestration

## Auth mode
Cookie / session via persistent Playwright storage state (user-initiated browser login, then session reused indefinitely).

## Gotchas
- Web UI selectors break frequently — the project deliberately uses OpenCV template matching for state detection (Pattern 3 in code-guide) instead of relying on selectors alone.

## See also
- [[_index]]
- [[Playwright]]
- [[OpenCV]]
