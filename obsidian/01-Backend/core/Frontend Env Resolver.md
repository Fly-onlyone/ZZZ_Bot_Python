---
tags: [backend, core]
---

# Frontend Env Resolver

> Resolves the Vite-time Sentry DSN for the React frontend by walking a fallback chain: explicit Vite env, root backend env, persisted settings.

## Source

- `backend/core/frontend_env.py` — primary implementation

## How it works

`resolve_frontend_sentry_dsn(runtime_env, settings_frontend_dsn)` returns a `(dsn, source)` tuple after checking, in order:

1. `runtime_env["VITE_SENTRY_DSN"]` → source `"env:VITE_SENTRY_DSN"`
2. `runtime_env["SENTRY_FRONTEND_DSN"]` → source `"env:SENTRY_FRONTEND_DSN"`
3. `settings_frontend_dsn.strip()` → source `"settings.sentry_frontend_dsn"`
4. Otherwise `("", "disabled")`

The source string is logged at startup so operators can confirm which layer supplied the DSN — important when the advanced settings UI overrides a missing env var across restarts.

## Depends on

- [[Settings Contract]] — `sentry_frontend_dsn` is part of the advanced settings whitelist
- [[GlobalVar]] — `settings.sentry_frontend_dsn`

## Used by

- [[Bot Entry Point]] — called before launching the Vite dev server
- [[Sentry Logger]] — frontend reads `VITE_SENTRY_DSN` at build/runtime

## Gotchas

- Source labels survive into logs; do not change them without grepping observability dashboards.

## See also

- [[_index]]
- [[Sentry]]
