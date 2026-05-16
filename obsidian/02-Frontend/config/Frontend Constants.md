---
tags: [frontend, config]
---

# Frontend Constants

> Central source of truth for backend URL, cache stale times, layout dimensions, retry counts, and password-field detection.

## Source
- `frontend/src/config/constants.js` — primary

## How it works
- `BACKEND_URL` — `import.meta.env.VITE_BACKEND_URL` if defined, else `http://127.0.0.1:8000`. Dev reads `frontend/.env.development` (port 8001); production builds drop the env and hit the bundled sidecar on 8000. See [[Frontend Env Resolver]] and [[Port Configuration]].
- `STALE_TIMES` — per-route TanStack Query stale windows: `shopping` 15min, `redeem` 10min, `settings` 60min, `account` 30min, mission/hunt 5min, backup-summary 2min, locator-tracker 2min, etc.
- `DEFAULT_STALE_TIME` — 1min fallback.
- `DRAWER_WIDTH` — 240px nav drawer.
- `HEADER_HEIGHT` — 64px app bar.
- `DEFAULT_PRIORITY_OFFSET` — 1 (priorities start at 1).
- `API_RETRY_COUNT` — 2 retries for `useRouteData`/`useSaveData`.
- `PASSWORD_FIELD_KEYWORDS` — `["password"]`, used by [[useFieldRenderer]] to mask inputs.

## Used by
- [[DataLoader]], [[useTaskEvents]], [[useShoppingState]], [[useFieldRenderer]], [[NavigationDrawer]], [[AppHeader]]

## See also
- [[_index]]
- [[Port Configuration]]
- [[Frontend Env Resolver]]
