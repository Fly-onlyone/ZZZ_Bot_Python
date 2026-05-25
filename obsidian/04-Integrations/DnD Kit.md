---
tags: [integration]
---

# DnD Kit

> Drag-and-drop toolkit. Powers the [[Shopping Page]] priority reorder via a custom div-based sortable table.

## Used for
- [[ShoppingItemsTable]] — unified shopping table with selected rows at the top, draggable to reorder priority.

## Configuration
- `@dnd-kit/core ^6.3.1`
- `@dnd-kit/sortable ^10.0.0`
- `@dnd-kit/utilities ^3.2.2`

## Wire-up
- `frontend/src/components/common/ShoppingItemsTable.jsx` — `DndContext` + `SortableContext` wrapping rows. `useSortable` per row (selected rows only); `setActivatorNodeRef` on the leading drag-handle icon so the rest of the row stays clickable.
- `frontend/src/hooks/useShoppingState.js` — `handleDragEnd` consumes the dnd-kit event and `arrayMove`s `selectedRows`, reassigning sequential priorities.

## Gotcha — never combine with third-party table libraries
We tried two: **MUI X `DataGrid`** mutates row `style.transform` every render for virtualization, overwriting dnd-kit's drag transform and snapping rows back. **`material-react-table`** has its own HTML5-native row reorder; combining it with `enableRowPinning` + `select-sticky` causes MRT's internal `row.pin()` calls to fight externally-controlled state and silently break the drag handler. The reliable path is dnd-kit on plain MUI `Box` divs — no third-party table internals to fight with.

## Auth mode
N/A

## See also
- [[_index]]
- [[Shopping Page]]
- [[ShoppingItemsTable]]
