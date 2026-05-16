---
tags: [frontend, content]
---

# Running Status Section

> Inline row showing the Zhu Yuan avatar with last-run and next-run DateTimeFields.

## How it works
Reads `check-run-status` via [[DataLoader]] (`{last_run, next_run}`) and renders a horizontal flex row: animated Zhu Yuan icon (from [[Asset Endpoints]] `/images/Zhu Yuan02.ico`) with hover tilt, then "Last run" + read-only `DateTimeField` and "Next run" + `DateTimeField`. Times parse from `HH:mm DD/MM/YY` via [[Day.js]] into `DD/MM/YYYY - hh:mm A`.

If both `last_run` and `next_run` are missing it falls back to [[EmptyState]] with a Schedule icon. Stagger of children uses `containerVariants` / `itemVariants`. The compact dashboard equivalent is [[Compact Running Status]].

## Source
- `frontend/src/content/RunningStatus.jsx` — primary

## Depends on
- [[DataLoader]] — `check-run-status`
- [[Mission Endpoints]] — `/check-run-status`
- [[Day.js]] — time formatting

## See also
- [[_index]]
- [[Compact Running Status]]
- [[Mission Email Scheduler]]
