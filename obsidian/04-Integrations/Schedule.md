---
tags: [integration]
---

# Schedule

> Lightweight Python cron-like job scheduler that drives the daily task cycle at user-configured times (e.g. `08:00`, `20:00`).

## Used for
- [[Daily Task Cycle]] — fires `playwright_task()` at each `schedule_times` entry
- [[Mission Email Scheduler]] — periodic email summary
- [[Hunt Mode Lifecycle]] — polls for shop renewal window

## Configuration
- Version `schedule==1.2.2` (`pyproject.toml`)
- `schedule_times: ["08:00", "20:00"]` in `output/settings.json`
- Frontend Settings page can add/remove times; scheduler is rebuilt on save

## Wire-up
- `backend/core/Bot.py` (Bot Entry Point) — registers `schedule.every().day.at(t).do(...)` for each time
- Main loop calls `schedule.run_pending()` in a `time.sleep` poll loop

## Auth mode
N/A

## Gotchas
- Local time zone only — no UTC support out of the box; users in different time zones must adjust manually.
- `schedule` runs jobs synchronously on the polling thread, so long-running automation blocks the next tick — the project mitigates by running Playwright work in a separate task.

## See also
- [[_index]]
- [[Bot Entry Point]]
- [[Daily Task Cycle]]
