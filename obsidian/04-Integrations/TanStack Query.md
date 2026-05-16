---
tags: [integration]
---

# TanStack Query

> Server-state cache layer (`@tanstack/react-query`) that powers every API call from the frontend — handles caching, refetch, retries, optimistic updates.

## Used for
- All API fetches via [[DataLoader]]
- Auto-refresh of mission / hunt / shopping data
- Mutation flows for [[Shopping Page]], [[Redeem Page]], [[Settings Page]]
- Cache invalidation after [[Backup Endpoints]] import

## Configuration
- Version `@tanstack/react-query ^5.62.3` (`frontend/package.json`)
- Single shared `QueryClient` instantiated in [[Frontend Entry Point]] and wrapped via `QueryClientProvider`

## Wire-up
- `frontend/src/services/DataLoader.js` — typed query / mutation factories
- `frontend/src/main.jsx` — `QueryClientProvider`
- Page components — `useQuery` / `useMutation` consumers

## Auth mode
N/A (delegates to fetch, which targets the loopback backend)

## See also
- [[_index]]
- [[Frontend Data Flow]]
- [[DataLoader]]
