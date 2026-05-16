---
tags: [frontend, pages]
---

# Manual Login Page

> Launches a manual Playwright browser session at a chosen HoYoLab URL with start/stop polling.

## How it works
Three URL presets (MINO, REDEEM, CHECK_IN) feed a `Select`; the play/stop `IconButton` POSTs `{url, playState}` to `/manual` and, when starting, opens a `Sentry.startSpan` then polls `/playstate` every 500 ms until the backend reports the session closed.

While `playState` is true the URL dropdown is disabled and the stop icon glows red. Used inside the **Manual Browser** tab of [[Account Page]]; talks to [[ManualLoginManager]] through [[Account Endpoints]].

## Source
- `frontend/src/pages/ManualLogin.jsx` — primary

## Depends on
- [[Account Endpoints]] — `/manual`, `/playstate`
- [[Sentry Logger]] — span + structured logs
- [[ThemeContext]] — glow color

## Used by
- [[Account Page]] — Manual Browser tab

## Gotchas
- Polling interval is 500 ms — keep stop handling tight or spans leak; the component holds a `spanFinishRef` and clears it on stop, error, or backend-reported close.

## See also
- [[_index]]
- [[Manual Login Flow]]
