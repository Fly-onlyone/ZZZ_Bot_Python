---
tags: [frontend, content]
---

# Hunt Section

> Hunt-mode dashboard: active/paused state, hunted-item count, next-hunt time, and per-item schedule table.

## How it works
Fetches `overview/hunt` (`{enabled, hunt_items, next_hunt_time}`) via [[DataLoader]]. Three guard states render via [[EmptyState]]: disabled hunt mode (pause icon), enabled-but-empty list (search-off icon), and loading skeleton.

When active, two animated stat cards show "Hunt Mode Active" + items count, followed by an `AccessTimeIcon` + MUI X `DateTimeField` (read-only, `DD/MM/YYYY - hh:mm A`) parsed from `HH:mm DD/MM/YY` with [[Day.js]]. The schedule table lists each hunt item with a colored time chip (gray for `Not scheduled`/`Invalid time`) animated with `tableRowVariants`. Lazy-loaded inside [[Shopping Page]].

## Source
- `frontend/src/content/Hunt.jsx` — primary

## Depends on
- [[DataLoader]] — `overview/hunt`
- [[Mission Endpoints]] — `/overview/hunt`
- [[Day.js]] — time parsing

## Used by
- [[Shopping Page]] — Hunt Mode tab

## See also
- [[_index]]
- [[HuntModeHandler]]
- [[Hunt Mode Lifecycle]]
