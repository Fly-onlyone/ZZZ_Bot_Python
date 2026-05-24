---
tags: [moc, frontend, hooks]
---

# Frontend / hooks — Map of Content

> Custom hooks. State machinery for forms, server events, and UI scaling.

- [[useFormState]] — fetch + cache-mirrored edits + auto-save commit per route
- [[useAutoSave]] — debounced commit wrapper around useSaveData with status + retry
- [[useShoppingState]] — shopping list state with drag-drop reordering
- [[useFieldRenderer]] — maps field key → field component (Text, Boolean, Select, Array)
- [[useTaskEvents]] — SSE listener for backend task updates
- [[useZoom]] — zoom level state + context provider for UI scaling

## See also

- [[_HOME]]
- [[02-Frontend/_index|Frontend]]
- [[Frontend Data Flow]]
- [[Event Bus]]
- [[SSE Event Bus Pattern]]
