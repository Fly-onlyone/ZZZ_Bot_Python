---
tags: [integration]
---

# Day.js

> Lightweight date library wired into MUI X DatePickers as the date adapter — used for the mission report date filter on [[Overview Page]].

## Used for
- Date filtering on the mission overview
- Formatting timestamps in [[DataTable]] columns
- MUI X `LocalizationProvider` adapter

## Configuration
- Version `dayjs ^1.11.13` (`frontend/package.json`)
- Used with `@mui/x-date-pickers ^7.22.3` via `AdapterDayjs`

## Wire-up
- `frontend/src/main.jsx` or page-level — `<LocalizationProvider dateAdapter={AdapterDayjs}>`
- `frontend/src/pages/Overview Page.jsx` — date range pickers
- `frontend/src/content/Mission Section.jsx` — date formatting

## Auth mode
N/A

## Gotchas
- Day.js is immutable but `.add()` / `.subtract()` return new instances — don't mutate in place.

## See also
- [[_index]]
- [[MUI]]
- [[Overview Page]]
