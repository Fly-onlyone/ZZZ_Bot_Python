---
tags: [frontend, pages]
---

# Redeem Page

> DataGrid of pending redemption codes with per-row "DONE" toggle and auto-save.

## How it works
Loads the `redeem` list through [[DataLoader]] `useRouteData` and persists changes via [[useAutoSave]] keyed on `"redeem"`. Each row exposes `item_name`, `code`, `day`, a `state` icon (Done/Close), and an action button. Clicking **DONE** flips `state` locally; a `useEffect` watching `rows` then debounces a commit to [[Redeem Endpoints]] through `useAutoSave`. There is no submit button — the first hydration is suppressed by `hasHydratedRef` so the initial server load doesn't echo back. A [[SaveStatus]] pill above the grid surfaces saving/saved/error.

A `JSON.stringify` snapshot comparison prevents needless `setRows` re-renders when the server payload is unchanged. Lazy-loaded as a tab inside [[Shopping Page]] but also reachable as its own route via [[PermanentDrawer Router]].

## Source
- `frontend/src/pages/Redeem.jsx` — primary

## Depends on
- [[DataLoader]] — fetch
- [[useAutoSave]] — debounced save
- [[SaveStatus]] — feedback pill
- [[Redeem Endpoints]] — backend
- [[EmptyState]] — empty render

## Used by
- [[Shopping Page]] — Redeem Codes tab
- [[PermanentDrawer Router]] — route

## See also
- [[_index]]
- [[RedeemAutofill]]
