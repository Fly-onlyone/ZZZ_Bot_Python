---
tags: [frontend, pages]
---

# Monitoring Page

> Single-card Sentry configuration form (DSNs, test event, traces sample rate).

## How it works
Wraps [[ValueAdapter]] bound to the `settings` route with a custom `Monitoring` section exposing `sentry_dsn`, `sentry_frontend_dsn`, `sentry_send_test_event`, and `sentry_traces_sample_rate`. The sample rate uses a `select` override with discrete steps (1.0, 0.5, 0.25, 0.1) — see [[Dynamic Form ValueAdapter Pattern]].

No bespoke layout — relies entirely on ValueAdapter rendering. Mounted as a tab inside [[Tools Page]] and persists via [[Settings Endpoints]] like every other settings surface.

## Source
- `frontend/src/pages/MonitoringPage.jsx` — primary

## Depends on
- [[ValueAdapter]] — form rendering
- [[Settings Endpoints]] — `/settings`
- [[Sentry Logger]] — consumer of the DSN

## Used by
- [[Tools Page]] — Monitoring tab

## See also
- [[_index]]
- [[Sentry]]
