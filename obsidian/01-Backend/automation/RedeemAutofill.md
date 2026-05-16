---
tags: [backend, automation]
---

# RedeemAutofill

> Opens the redemption page, authenticates if needed, pastes the code, and persists the result with Sentry escalation when a captcha blocks login.

## Source
- `backend/automation/RedeemAutofill.py` — primary

## How it works
1. Pre-saves the code via [[DataHandler]] as `redeem_pending` so a crash never loses the gift code.
2. Opens `https://zenless.hoyoverse.com/redemption` in a fresh page; if the login banner appears, drives [[AutoLogin]] inside a `retry_until_screen_appears` loop.
3. Probes the iframe for five known captcha texts (`Slide to complete the puzzle`, `Complete verification`, etc.); a hit emits a Sentry warning with `redeem.manual_captcha_required=true`, notifies the user, and returns `manual_captcha_required`.
4. Selects the Asia server, fills `Enter redemption code`, clicks `Redeem`, and looks for the success popup.
5. `finally:` persists `storage_state`, updates the redemption record with the final status, and closes the page (keeping it open for visual confirmation when `hide_browser=False`).

## Depends on
- [[AutoLogin]] — credentialed login attempt
- [[RetryHelper]] — wait for login UI to stabilize
- [[DataHandler]] — `save_redeem_data` persistence
- [[NotificationHelper]] — toast notifications
- [[Storage State Store]] — context persistence
- [[Sentry]] — manual-captcha escalation

## Used by
- [[ShoppingHandler]] — redeem purchased item codes
- [[DrawHandler]] — redeem prize codes
- [[HuntModeHandler]] — phase-2 bulk redeem

## Gotchas
- Captcha detection list is brittle — HoYoLab adds new phrases periodically; missing matches fall through as `redeem_not_confirmed`.

## See also
- [[_index]]
- [[Three-Phase Hunt Execution Pattern]]
- [[Notification Pipeline]]
