---
tags: [frontend, services]
---

# DataLoader

> TanStack Query wrapper exposing route-based fetch/save/action/prefetch hooks plus a startup health probe.

## Source
- `frontend/src/services/DataLoader.jsx` — primary

## How it works
`DataLoader()` returns five hooks built on a shared `fetchJson(url, context, options)` helper that logs every failure to [[Sentry Logger]]:

- `useRouteData(route, opts)` — `useQuery` against `${BACKEND_URL}/${route}`. `staleTime` looks up `STALE_TIMES[route]` or falls back to `DEFAULT_STALE_TIME`. Retries `API_RETRY_COUNT` (2) times, no refetch on window focus.
- `useBackendHealth()` — probes `/health` with 12 startup retries and exponential backoff capped at 3s; 5s stale time.
- `useSaveData(route)` — POST `useMutation`. On success, invalidates keys from `RELATED_QUERY_KEYS_BY_ROUTE` (e.g. `backup/import` invalidates account, shopping, redeem, settings, hunt, mission, summary).
- `useActionData(route)` — POST `useMutation` for action endpoints; parses JSON error bodies.
- `prefetchRoutes(routes)` — `Promise.allSettled` over `queryClient.prefetchQuery`.

Re-exports `BACKEND_URL` for convenience.

## Depends on
- [[TanStack Query]] — `useQuery`, `useMutation`, `useQueryClient`
- [[Frontend Constants]] — `BACKEND_URL`, `STALE_TIMES`, `DEFAULT_STALE_TIME`, `API_RETRY_COUNT`
- [[Sentry Logger]] — request/parse/save telemetry

## Used by
- [[useFormState]], [[useTaskEvents]], [[ThemeContext]], [[PermanentDrawer Router]] — backend integration
- Most pages: [[Overview Page]], [[Shopping Page]], [[Settings Page]], [[Account Page]], [[Backup Page]], [[Locator Tracker Page]]

## See also
- [[_index]]
- [[Frontend Data Flow]]
- [[SSE Event Bus Pattern]]
