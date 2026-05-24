---
tags: [frontend, hooks]
---

# useFormState

> Route-based form lifecycle hook: fetches data, mirrors edits into the
> TanStack cache, and persists changes through [[useAutoSave]].

## Source
- `frontend/src/hooks/useFormState.js` — primary

## How it works
1. Derives the route key from `useLocation().pathname` (or an explicit `routeOverride`).
2. Calls `useRouteData(route)` from [[DataLoader]] for the current value and `useAutoSave(route)` for the persistence side.
3. `handleChange(key, newValue)` writes optimistically into the TanStack Query cache via `queryClient.setQueryData([route], …)` — no local React state for the form body.
4. `commit()` reads the latest cache snapshot via `queryClient.getQueryData([route])` and hands it to `useAutoSave.commit`, which debounces and persists it. There is no submit button or handler; callers invoke `commit` from per-field blur/change events.
5. Returns `{ value, error, handleChange, commit, autoSave, route }` — `autoSave` carries the `status` / `error` / `retry` surface that [[ValueAdapter]] forwards to [[SaveStatus]].

## Depends on
- [[DataLoader]] — fetch + save layer
- [[useAutoSave]] — debounced commit + status
- [[TanStack Query]] — cache as the source of truth

## Used by
- [[Account Page]], [[Settings Page]] — single-route edit screens
- [[ValueAdapter]] — paired with [[useFieldRenderer]] and [[SaveStatus]]

## Gotchas
- Edits live only in the query cache until `commit` flushes through
  `useAutoSave`. A manual `invalidateQueries` between an edit and the commit
  fire (within the 300ms debounce) will discard the unsaved change.

## See also
- [[_index]]
- [[useAutoSave]]
- [[useFieldRenderer]]
- [[Frontend Data Flow]]
