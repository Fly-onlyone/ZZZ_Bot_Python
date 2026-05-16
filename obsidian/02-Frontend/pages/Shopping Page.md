---
tags: [frontend, pages]
---

# Shopping Page

> Tabbed shop manager with item grid, priority drag-sort, redeem codes, and hunt mode editor.

## How it works
Three Aurora-styled tabs: **Items**, **Redeem Codes** (lazy [[Redeem Page]]), **Hunt Mode** (lazy [[Hunt Section]]). The Items tab loads `shopping` data via [[DataLoader]] `useRouteData` and pushes a save payload (`Selected`, `Hunt`) with `useSaveData`.

The grid uses MUI X `DataGrid` with checkbox selection, an editable `Priority` column (only editable for selected rows), and a Hunt icon column driven by [[useShoppingState]]. [[SortableSelectedItems]] above the grid handles priority reordering via [[DnD Kit]]. Purchased rows render with a green tint; hunt rows with amber. Tab transitions use `auroraPanelVariants` from [[Aurora Tab Styles]].

## Source
- `frontend/src/pages/Shopping.jsx` — primary

## Depends on
- [[DataLoader]] — fetch/save
- [[useShoppingState]] — selection + hunt state
- [[SortableSelectedItems]] — priority DnD
- [[Shopping Endpoints]] — backend

## See also
- [[_index]]
- [[ShoppingHandler]]
