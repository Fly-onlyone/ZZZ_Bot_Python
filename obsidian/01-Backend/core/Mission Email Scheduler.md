---
tags: [backend, core]
---

# Mission Email Scheduler

> Tiny dispatcher that either fires the mission email synchronously (before process exit) or hands it to a daemon thread so the automation can continue without waiting on SMTP.

## Source

- `backend/core/mission_email.py` — primary implementation

## How it works

`schedule_mission_email_delivery(todays_data, *, exit_after_run, send_func, thread_factory)` deep-copies the payload so caller-side mutations after dispatch cannot race the email worker. If `exit_after_run` is set, it calls `send_func(payload)` inline and returns `None`. Otherwise it spins a daemon `Thread` named `mission-email-sender` and returns the handle.

The `thread_factory` parameter is for tests — production passes the default `threading.Thread`.

## Depends on

- *(no runtime dependencies beyond stdlib)*

## Used by

- [[Bot Entry Point]] — `playwright_task()` calls this with `_send_mission_email` as `send_func`
- [[Notification Sender]] — invoked indirectly via the wrapped sender

## Gotchas

- Sync mode is required when `exit_after_run=True` because the process would otherwise terminate before the daemon thread sends.
- Deep copy is essential — `todays_data` is mutated by later phases (hunt cleanup, etc.).

## See also

- [[_index]]
- [[Notification Pipeline]]
