---
tags: [backend, core]
---

# Settings Contract

> Whitelist of advanced setting keys that the Advanced Settings UI is allowed to read and persist, gating the rest of `AppSettings`.

## Source

- `backend/core/settings_contract.py` — primary implementation

## How it works

`ADVANCED_SETTINGS_KEYS` is a frozen tuple covering window/exit behavior (`show_window_on_startup`, `exit_after_run`), hunt polling (`hunt_poll_max_wait_seconds`, `hunt_poll_interval_seconds`, `hunt_poll_backoff_enabled`, `hunt_early_exit_on_unavailable`), and Sentry knobs (`sentry_dsn`, `sentry_frontend_dsn`, `sentry_send_test_event`, `sentry_traces_sample_rate`).

`extract_advanced_settings(payload)` returns a new dict containing only the keys from the whitelist that are present in the payload — no validation, no defaults, just a filter.

This stops the Advanced page from accidentally persisting unrelated fields (schedule, theme, account credentials) that have their own dedicated forms.

## Depends on

- *(no runtime dependencies)*

## Used by

- [[Settings Endpoints]] — Advanced GET/POST routes
- [[Settings Page]] — the React Advanced tab roundtrips via these keys

## Gotchas

- Adding a new advanced field requires editing **this tuple** in addition to `AppSettings`.

## See also

- [[_index]]
- [[GlobalVar]]
