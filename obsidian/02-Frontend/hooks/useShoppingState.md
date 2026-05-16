---
tags: [frontend, hooks]
---

# useShoppingState

> Owns the Shopping page's selected items and hunt-list state, including drag-reorder and priority sync.

## Source
- `frontend/src/hooks/useShoppingState.js` — primary

## How it works
1. Hydrates `selectedRows` (`{Name, Priority}`) and `huntItems` (string names) from the shopping payload on every prop change.
2. `handleRowSelectionChange` reconciles DataGrid selection — keeps existing priorities, auto-prunes hunt entries that are no longer selected.
3. `handleHuntToggle` flips an item in/out of `huntItems`.
4. `handleDragEnd` calls `arrayMove` from [[DnD Kit]] then renumbers priorities sequentially starting at `DEFAULT_PRIORITY_OFFSET` (from [[Frontend Constants]]).
5. `handlePriorityEdit` clamps the new value, moves the row, and reassigns priorities.

## Depends on
- [[DnD Kit]] — `arrayMove` for reorder
- [[Frontend Constants]] — `DEFAULT_PRIORITY_OFFSET`

## Used by
- [[Shopping Page]] — top-level state owner
- [[SortableSelectedItems]] — drag-drop list consumer

## Gotchas
- Hunt list is a strict subset of selected; deselecting in the grid silently removes the item from hunt without confirmation.

## See also
- [[_index]]
- [[Shopping Page]]
- [[Three-Phase Hunt Execution Pattern]]
