---
tags: [frontend, pages]
---

# Shopping Page

> Tabbed shop manager. The Items tab is a unified custom table built on plain MUI `Box` divs + [[DnD Kit]] — selected items pinned to the top in priority order (drag to reorder).

## How it works
Three Aurora-styled tabs: **Items**, **Redeem Codes** (lazy [[Redeem Page]]), **Hunt Mode** (lazy [[Hunt Section]]). The Items tab loads `shopping` data plus `settings` gate data via [[DataLoader]] `useRouteData` and persists changes through [[useAutoSave]] keyed on `"shopping"`. `useShoppingState` fires an `onChange` callback only for user edits; Shopping writes the pending `{ Selected, Hunt }` into the `shopping` cache, mirrors the derived `overview/hunt` cache using both `run_task` and `enable_hunt_mode` so the Hunt tab updates immediately, then debounces the backend save. A [[SaveStatus]] pill in the header row reports saving/saved/error.

The body is a single [[ShoppingItemsTable]] component:

- Selected rows render at the top in priority order. Each non-purchased selected row gets a drag handle that calls `useSortable` from [[DnD Kit]]. Drop reorders priority and fires the auto-save.
- A small "Catalog · N items" divider, then unselected (and unselected purchased) rows render below as plain non-draggable rows.
- Single checkbox column toggles selection: checking a catalog row promotes it to the bottom of the selected section; unchecking a selected row drops it back into the catalog.
- Hunt checkbox is interactive on selected non-purchased rows, with a tooltipped disabled state otherwise.
- Purchased rows render with a green tint, hunt-active rows with amber.

`useShoppingState.selectedRows` is the single source of truth; the table is derived from it via `useMemo` (selected section in priority order, catalog section in `Object.entries(itemList)` order with purchased first).

## Source
- `frontend/src/pages/Shopping.jsx` — primary

## Depends on
- [[DataLoader]] — fetch
- [[useAutoSave]] — debounced save
- [[SaveStatus]] — feedback pill
- [[useShoppingState]] — selection + hunt state + reorder logic
- [[ShoppingItemsTable]] — the unified table component
- [[DnD Kit]] — drag-to-reorder primitives
- [[Shopping Endpoints]] — backend

## Gotchas
- Item `Name` is the sortable id and must be unique across the catalog (backend invariant).
- Don't try to use MUI X `DataGrid` or `material-react-table` here. The DataGrid's virtualization mutates `style.transform` per render, breaking dnd-kit's drag transform; MRT's `select-sticky` row pinning mode internally calls `row.pin()` which fights externally-controlled state and silently breaks drag. The reliable path is dnd-kit on plain MUI `Box` divs — see [[DnD Kit]] for the full history.

## See also
- [[_index]]
- [[ShoppingHandler]]
