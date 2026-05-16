---
tags: [integration]
---

# React Router

> Client-side routing for the SPA — maps URL paths to page components rendered inside the permanent drawer layout.

## Used for
- Route definitions for Overview, Shopping, Redeem, Manual Login, Locator Tracker, Backup, Settings, Account, Tools, Monitoring, Logs
- Programmatic navigation from the drawer + tray Run Playwright trigger
- Dynamic route discovery via `/routes` endpoint (consumed by [[PermanentDrawer Router]])

## Configuration
- Version `react-router-dom ^7.0.0` (`frontend/package.json`)
- Uses `createBrowserRouter` (or `BrowserRouter` — see entry point)
- Routes co-located with [[PermanentDrawer Router]]

## Wire-up
- `frontend/src/main.jsx` — router provider
- `frontend/src/routes/` — route configuration + drawer
- `frontend/src/pages/*` — route components

## Auth mode
N/A

## Gotchas
- Tauri WebView serves from `tauri://localhost` — `BrowserRouter` works because the WebView treats it like HTTP. `HashRouter` is unnecessary.

## See also
- [[_index]]
- [[PermanentDrawer Router]]
- [[NavigationDrawer]]
