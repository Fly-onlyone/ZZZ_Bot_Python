---
tags: [frontend, pages]
---

# Redeem Page

> DataGrid of pending redemption codes with per-row "DONE" toggle and save.

## How it works
Loads the `redeem` list through [[DataLoader]] `useRouteData` and writes back via `useSaveData`. Each row exposes `item_name`, `code`, `day`, a `state` icon (Done/Close), and an action button. Clicking **DONE** flips `state` locally; **Save** persists the entire row set to [[Redeem Endpoints]].

A `JSON.stringify` snapshot comparison prevents needless `setRows` re-renders when the server payload is unchanged. Lazy-loaded as a tab inside [[Shopping Page]] but also reachable as its own route via [[PermanentDrawer Router]].

## Source
- `frontend/src/pages/Redeem.jsx` — primary

## Depends on
- [[DataLoader]] — fetch/save
- [[Redeem Endpoints]] — backend
- [[EmptyState]] — empty render
- [[SaveButton]] — submit

## Used by
- [[Shopping Page]] — Redeem Codes tab
- [[PermanentDrawer Router]] — route

## See also
- [[_index]]
- [[RedeemAutofill]]
