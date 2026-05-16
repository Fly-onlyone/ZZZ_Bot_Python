---
tags: [frontend, pages]
---

# Tools Page

> Tab container hosting Logs, Backup, Monitoring, and Locator inspectors as lazy children.

## How it works
Four Aurora tabs each render a `React.lazy` import — [[Logs Page]], [[Backup Page]], [[Monitoring Page]], [[Locator Tracker Page]] — wrapped in a `Suspense` fallback (`CircularProgress` + "Loading tool panel..."). The wrapper uses `flex: 1; minHeight: 0` so child panels (especially Logs) can manage their own internal scroll.

Tab switches animate via `auroraPanelVariants`; the panel `key` is the active index to force remount and let the lazy chunk swap cleanly. Reachable via [[PermanentDrawer Router]].

## Source
- `frontend/src/pages/ToolsPage.jsx` — primary

## Depends on
- [[Logs Page]] — child tab
- [[Backup Page]] — child tab
- [[Monitoring Page]] — child tab
- [[Locator Tracker Page]] — child tab
- [[Aurora Tab Styles]] — panel variants

## See also
- [[_index]]
- [[Frontend Data Flow]]
