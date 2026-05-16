---
tags: [frontend, content]
---

# Compact Running Status

> Three-card overview banner: last run, next run, and hunt status with item count.

## How it works
Renders inside the [[Overview Page]] as a wide `Paper` with hover lift. The left side is the Zhu Yuan avatar from [[Asset Endpoints]] with `whileHover` rotate/scale; the right is a 3-column grid of [[Framer Motion]] cards:

1. **Last Run** — `runStatus.last_run` (em dash if absent).
2. **Next Run** — `runStatus.next_run`.
3. **Hunt Status** — green CheckCircle + "N Items" when `huntInfo.enabled && hunt_items.length > 0`, else gray Pause + "Disabled".

Data comes from two parallel [[DataLoader]] queries: `check-run-status` and `overview/hunt`. Renders `null` until `runStatus` resolves (no skeleton).

## Source
- `frontend/src/content/CompactRunningStatus.jsx` — primary

## Depends on
- [[DataLoader]] — both queries
- [[Mission Endpoints]] — `/check-run-status`, `/overview/hunt`
- [[ThemeContext]] — gradients + glow

## Used by
- [[Overview Page]] — top banner

## See also
- [[_index]]
- [[Running Status Section]]
