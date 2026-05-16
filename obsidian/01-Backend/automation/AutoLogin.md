---
tags: [backend, automation]
---

# AutoLogin

> Fills the HoYoLab login iframe with stored credentials and submits the form.

## Source
- `backend/automation/AutoLogin.py` — primary

## How it works
1. Calls `ensure_accounts_loaded()` so `accounts.hoyo_username` / `hoyo_password` are populated from [[MongoRepository]].
2. Resolves the iframe via `page.locator("#hyv-account-frame").content_frame`.
3. Fills `input[name="username"]` and `input[name="password"]`, then clicks the `Log In` button.
4. Waits 5 s for the post-login redirect to settle.

The module is intentionally tiny — a single `run(page)` function callable from any handler that lands on the login screen.

## Depends on
- [[GlobalVar]] — `accounts` singleton + lazy loader
- [[Playwright]] — iframe content frame access

## Used by
- [[RedeemAutofill]] — automatic redeem login
- [[ManualLoginManager]] — initial credentialed login

## Gotchas
- Captcha-protected logins won't complete here — [[RedeemAutofill]] detects the resulting captcha overlays and escalates to manual login.

## See also
- [[_index]]
- [[Manual Login Flow]]
- [[RedeemAutofill]]
