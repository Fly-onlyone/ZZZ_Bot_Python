---
tags: [integration]
---

# DnD Kit

> Drag-and-drop toolkit used for reordering selected shopping items by priority on the [[Shopping Page]].

## Used for
- [[SortableSelectedItems]] — drag-to-reorder list on Shopping page
- Priority order persisted to the `Selected` array in `output/shopping.json`

## Configuration
- `@dnd-kit/core ^6.3.1`
- `@dnd-kit/sortable ^10.0.0`
- `@dnd-kit/utilities ^3.2.2`

## Wire-up
- `frontend/src/components/common/SortableSelectedItems.jsx` — `DndContext` + `SortableContext`
- `frontend/src/hooks/useShoppingState.js` — state management for the reorderable list

## Auth mode
N/A

## See also
- [[_index]]
- [[Shopping Page]]
- [[SortableSelectedItems]]
