---
tags: [frontend, entry]
---

# Frontend Entry Point

> Boots Sentry, React 18, TanStack Query, theme + date providers, and mounts the router behind an error boundary.

## How it works
1. Reads `VITE_SENTRY_DSN`; if present and not already initialized (`__ZZZ_BOT_SENTRY_INITIALIZED__` guard), calls `Sentry.init` with the React Router v7 browser tracing integration, console capture + logging integrations, and the HTTP client integration. `tracesSampleRate` defaults to `1.0` in development and `0.1` in production, overridable via `VITE_SENTRY_TRACES_SAMPLE_RATE`.
2. Creates a singleton `QueryClient` with `gcTime: 2 minutes` and `refetchOnWindowFocus: false`.
3. Renders the tree as `<StrictMode><Sentry.ErrorBoundary fallback={ErrorFallback}><App/></ErrorBoundary></StrictMode>`. `App` wraps `QueryClientProvider` → [[ThemeContext]] `ThemeContextProvider` → `ThemedApp`, which builds the active MUI theme via [[MUI Theme Factory]] (memoized on theme name + prefers-dark + colors) and mounts `LocalizationProvider` ([[Day.js]] adapter) → `ThemeProvider` → [[PermanentDrawer Router]].
4. The React root is cached on `window.__ZZZ_BOT_APP_ROOT__` so hot-module replacement does not double-create roots, and a one-shot Sentry `logger.info` fires on first boot.

## Source
- `frontend/src/main.jsx` — primary

## Depends on
- [[Sentry]], [[Sentry Logger]]
- [[React]], [[React Router]]
- [[TanStack Query]]
- [[MUI]], [[MUI Theme Factory]], [[Day.js]]
- [[ThemeContext]]
- [[ErrorFallback]]
- [[PermanentDrawer Router]]
- [[Global CSS]]

## Used by
- [[Vite]] — entry referenced from `index.html`

## See also
- [[_index]]
- [[Global CSS]]
- [[Frontend Env Resolver]]
- [[Frontend Data Flow]]
