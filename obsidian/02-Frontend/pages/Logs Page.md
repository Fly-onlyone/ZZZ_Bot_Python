---
tags: [frontend, pages]
---

# Logs Page

> Filterable, paginated log viewer with level chips, search, and 5 s auto-refresh.

## How it works
Calls `/logs` directly with `useQuery` (bypassing [[DataLoader]]) keyed by file/levels/search/page; debounces search input by 300 ms and re-paginates on filter change. Returns `{files, entries, total}` from [[Health Endpoints]].

The toolbar exposes a file dropdown (current `app.log` + rotated `app.log.YYYY-MM-DD`), five toggleable `LEVELS` chips (`DEBUG…CRITICAL` with per-level color), a search box, an auto-refresh switch (5 s `refetchInterval`), and manual refresh. The table body uses sticky `thead` and `LEVEL_COLORS` for chip + hover tinting. Page size is 50.

## Source
- `frontend/src/pages/Logs.jsx` — primary

## Depends on
- [[Health Endpoints]] — `/logs`
- [[TanStack Query]] — fetch + polling
- [[SectionCard]] — shell

## Used by
- [[Tools Page]] — Logs tab

## See also
- [[_index]]
- [[Logger]]
- [[Logging Setup]]
