---
tags: [frontend, components, common]
---

# ShoppingItemsTable

> Unified shopping items table for the [[Shopping Page]] Items tab. Pure MUI `Box`-based grid layout with [[DnD Kit]] for priority drag-reorder. Selected items at the top (draggable), catalog items below (static).

## How it works
- Outer wrapper: sticky-headered, scrollable `Box` with rounded border and theme alpha background.
- **Header row** — CSS grid (`gridTemplateColumns: 44px 56px minmax(200px, 1fr) 80px 80px 130px 80px 64px`) of column labels (drag, select, Name, Price, Stock, Status, Priority, Hunt). `position: sticky; top: 0`.
- **`DndContext` + `SortableContext`** wraps the body. `items` are the names of selected, non-purchased rows only — purchased rows render in the selected section but `useSortable` is disabled on them so they can't be dragged.
- **`SortableShoppingRow`** — calls `useSortable({ id: row.Name })`, applies `CSS.Transform.toString(transform)` + `transition` to a `Box` row, and uses `setActivatorNodeRef` on the drag-handle `DragIndicatorIcon` so the rest of the row stays clickable. Each row uses the SAME `gridTemplateColumns` as the header so columns align.
- **`SectionDivider`** between selected and catalog ("Catalog · N items"). Hidden when one section is empty.
- **Catalog section** renders plain `ShoppingRow`s (no `useSortable`) below the SortableContext, so they're not drop targets.
- Visual treatments via `sx`: purchased rows get a green tint (`COMMON_COLORS.success.main` ~14% alpha) + green text, hunt rows get amber tint, dragging rows get `opacity: 0.7` + `GLOW.strong` halo + `zIndex: 10`.
- Hunt checkbox: interactive on selected non-purchased rows; a disabled tooltipped checkbox otherwise.

## Source
- `frontend/src/components/common/ShoppingItemsTable.jsx` — primary

## Depends on
- [[DnD Kit]] — `@dnd-kit/core`, `/sortable`, `/utilities`
- [[ThemeContext]] — themeColors
- [[Theme Styles]] — `GLOW.strong`

## Used by
- [[Shopping Page]] — entire Items tab body

## Gotchas
- Sortable IDs are `row.Name` (must match `useShoppingState`'s lookup). Duplicate item names would collide — backend enforces uniqueness.
- The drag handle uses `setActivatorNodeRef` (not `setNodeRef`) so the rest of the row remains a non-draggable click surface for the checkbox column.
- `touch-action: none` on the handle is required so mobile touch drags don't get hijacked by scroll.
- DO NOT swap the underlying `Box` divs for a third-party table library — see [[DnD Kit]] for the history of failed attempts with MUI X DataGrid and Material React Table.

## See also
- [[_index]]
- [[Shopping Page]]
- [[useShoppingState]]
