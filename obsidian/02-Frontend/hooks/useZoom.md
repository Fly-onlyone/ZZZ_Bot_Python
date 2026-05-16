---
tags: [frontend, hooks]
---

# useZoom

> Persistent UI zoom level (0.5x–2.0x) controlled by buttons or Ctrl+wheel, scoped via a React context provider.

## Source
- `frontend/src/hooks/useZoom.jsx` — primary

## How it works
1. `ZoomProvider({ children, containerRef })` seeds `zoomLevel` from `localStorage["zzz-bot-zoom"]`, clamped to `[0.5, 2.0]` with 0.1 steps.
2. Persists every change back to localStorage via effect.
3. Exposes `zoomIn`, `zoomOut`, `resetZoom` callbacks; clamping rounds to one decimal place.
4. Attaches a non-passive `wheel` listener to `containerRef.current` — when Ctrl is held, scroll wheel adjusts zoom and `preventDefault()` blocks the browser's native zoom.
5. `useZoom()` exposes the context for consumers.

## Depends on
- React context + `localStorage`

## Used by
- [[PermanentDrawer Router]] — wraps layout in `<ZoomProvider>` and applies `zoom` + scaled `100dvh`
- [[NavigationDrawer]] / [[AppHeader]] — zoom buttons

## Gotchas
- Uses the CSS `zoom` property (not `transform: scale`), so layouts that rely on `vh`/`dvh` need the `calc(100dvh / ${zoomLevel})` compensation seen in PermanentDrawer.

## See also
- [[_index]]
- [[PermanentDrawer Router]]
