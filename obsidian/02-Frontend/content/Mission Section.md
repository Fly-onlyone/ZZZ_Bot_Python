---
tags: [frontend, content]
---

# Mission Section

> Mission report block: current day, check-in status, login reward screenshot, and per-mission status table.

## How it works
Reads `overview/mission` via [[DataLoader]]. Renders two stat cards (Current Day, Check-in status — green if `Login Success`, red otherwise) and, on success, a login-reward screenshot fetched from `/assets/screenshot/login_reward.png?day=…` ([[Asset Endpoints]]).

Below sits a table of `{name, state}` rows with a `Finished`/`Unfinished` chip (CheckCircle vs Error icon) and per-row success/failure background tint. Animations: `containerVariants` staggers children by 0.1 s; `tableRowVariants` slides each row in `x: -20 → 0` with a per-index delay; check-in panel transitions via `AnimatePresence`.

## Source
- `frontend/src/content/Mission.jsx` — primary

## Depends on
- [[DataLoader]] — `overview/mission`
- [[Mission Endpoints]] — backend
- [[Asset Endpoints]] — login reward image
- [[Framer Motion]] — stagger

## Used by
- [[Overview Page]] — Mission Report card

## See also
- [[_index]]
- [[MissionHandler]]
