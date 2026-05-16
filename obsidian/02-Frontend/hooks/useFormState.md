---
tags: [frontend, hooks]
---

# useFormState

> Route-based form lifecycle hook: fetches data, tracks edits, and persists changes with optimistic cache updates.

## Source
- `frontend/src/hooks/useFormState.js` — primary

## How it works
1. Derives the route key from `useLocation().pathname` (or an explicit `routeOverride`).
2. Calls `useRouteData(route)` from [[DataLoader]] for the current value and `useSaveData(route)` for the mutation.
3. `handleChange(key, newValue)` writes optimistically into the TanStack Query cache via `queryClient.setQueryData([route], …)` — no local React state for the form body.
4. `handleSubmit` triggers the mutation and surfaces success/error through a local `alert` state. Both outcomes log to [[Sentry Logger]].

## Depends on
- [[DataLoader]] — fetch + save layer
- [[TanStack Query]] — cache as the source of truth
- [[Sentry Logger]] — telemetry on save outcomes

## Used by
- [[Account Page]], [[Settings Page]] — single-route edit screens
- [[ValueAdapter]] — paired with [[useFieldRenderer]]

## Gotchas
- Edits live only in the query cache until `handleSubmit`; a manual `invalidateQueries` will discard unsaved changes.

## See also
- [[_index]]
- [[useFieldRenderer]]
- [[Frontend Data Flow]]
