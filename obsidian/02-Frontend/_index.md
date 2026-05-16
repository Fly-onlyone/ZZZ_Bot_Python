---
tags: [moc, frontend]
---

# Frontend — Map of Content

> React 18 + MUI v6 + TanStack Query + Framer Motion. Bundled with Vite (dev) and
> served as static assets in production (Tauri WebView loads `frontend/dist/`).
> Communicates with the backend over REST (DataLoader) + SSE (useTaskEvents).

## Subzones

- [[02-Frontend/pages/_index|pages]] — top-level route components
- [[02-Frontend/content/_index|content]] — reusable page sections
- [[02-Frontend/components/_index|components]] — common / fields / layout / forms
- [[02-Frontend/hooks/_index|hooks]] — form state, SSE, drag-drop, zoom
- [[02-Frontend/services/_index|services]] — DataLoader (TanStack Query) + Sentry
- [[02-Frontend/theme/_index|theme]] — 4-theme system + MUI overrides + glow utilities
- [[02-Frontend/config/_index|config]] — constants, stale times
- [[02-Frontend/routes/_index|routes]] — PermanentDrawer router with lazy loading
- [[02-Frontend/entry/_index|entry]] — main.jsx, index.css

## See also

- [[_HOME]]
- [[Frontend Data Flow]]
- [[01-Backend/_index|Backend]]
- [[03-Desktop/_index|Desktop]]
