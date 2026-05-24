---
tags: [frontend, pages]
---

# Shopping Page

> Tabbed shop manager with item grid, priority drag-sort, redeem codes, and hunt mode editor. Selection + hunt edits auto-save.

## How it works
Three Aurora-styled tabs: **Items**, **Redeem Codes** (lazy [[Redeem Page]]), **Hunt Mode** (lazy [[Hunt Section]]). The Items tab loads `shopping` data via [[DataLoader]] `useRouteData` and persists changes through [[useAutoSave]] keyed on `"shopping"`. A `useEffect` watching `selectedRows` + `huntItems` debounces a `{ Selected, Hunt }` commit on every checkbox toggle, drag-reorder, inline-priority edit, or Hunt toggle — `hasHydratedRef` suppresses the very first run so the initial hydration from the server doesn't trigger a save. A [[SaveStatus]] pill in the header row reports saving/saved/error.

The grid uses MUI X `DataGrid` with checkbox selection, an editable `Priority` column (only editable for selected rows), and a Hunt icon column driven by [[useShoppingState]]. [[SortableSelectedItems]] above the grid handles priority reordering via [[DnD Kit]]. Purchased rows render with a green tint; hunt rows with amber. Tab transitions use `auroraPanelVariants` from [[Aurora Tab Styles]].

## Source
- `frontend/src/pages/Shopping.jsx` — primary

## Depends on
- [[DataLoader]] — fetch
- [[useAutoSave]] — debounced save
- [[SaveStatus]] — feedback pill
- [[useShoppingState]] — selection + hunt state
- [[SortableSelectedItems]] — priority DnD
- [[Shopping Endpoints]] — backend

## See also
- [[_index]]
- [[ShoppingHandler]]
