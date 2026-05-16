---
tags: [integration]
---

# Sentry

> Error / performance monitoring for both the Python backend (Sentry SDK with FastAPI integration) and the React frontend (`@sentry/react`).

## Used for
- Backend uncaught exception tracking + FastAPI request traces
- Frontend error boundaries via [[ErrorFallback]] + [[Sentry Logger]]
- Production error visibility (no local user reports needed)

## Configuration
- Backend: `sentry-sdk[fastapi]>=2.0` (`pyproject.toml`)
- Frontend: `@sentry/react ^9.41.0` (`frontend/package.json`)
- DSN sources (Rust shell, `resolve_sidecar_sentry_dsn()`): runtime env `SENTRY_DSN`, then build-time `option_env!("ZZZ_SENTRY_DSN")`
- DSN injected into the sidecar process via `SENTRY_DSN` env at spawn time
- CSP allows `https://*.ingest.us.sentry.io` (`tauri.conf.json`)

## Wire-up
- `backend/core/Bot.py` — Sentry SDK init (FastAPI integration)
- `frontend/src/services/Sentry Logger.js` — frontend init + capture helpers
- `frontend/src/components/common/ErrorFallback.jsx` — captures render errors
- `src-tauri/src/lib.rs` — DSN resolution + env injection into sidecar

## Auth mode
DSN (Sentry public key); no further auth needed.

## Gotchas
- `BotSidecar.spec` excludes `sentry_sdk.integrations.mcp` (and `fastmcp`, `mcp`, `mcp_tools`) to keep the bundle small — re-enable if MCP usage is added.

## See also
- [[_index]]
- [[Sidecar Spawn]]
- [[Sentry Logger]]
