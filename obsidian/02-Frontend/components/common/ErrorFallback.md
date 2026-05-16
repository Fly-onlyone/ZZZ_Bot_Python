---
tags: [frontend, components, common]
---

# ErrorFallback

> Full-viewport fallback UI rendered by the Sentry ErrorBoundary when the app throws.

## How it works
A centered `Box` (`minHeight: 100vh`) shows a Tabler `IconAlertTriangle`, the heading "Something went wrong", `error.message` (or a generic fallback), and a "Try again" outlined button that calls `resetError`. The container carries a red `GLOW.medium("#ef4444")` shadow from [[Theme Styles]]. Props `{ error, resetError }` match the Sentry ErrorBoundary fallback signature.

## Source
- `frontend/src/components/common/ErrorFallback.jsx` — primary

## Depends on
- [[Theme Styles]] — `GLOW.medium`
- [[Sentry]] — fallback contract

## Used by
- [[Frontend Entry Point]] — wraps `<App />` in `Sentry.ErrorBoundary`

## Gotchas
- Does NOT consume [[ThemeContext]] — must work even if context fails to mount.

## See also
- [[_index]]
- [[Frontend Entry Point]]
- [[Sentry Logger]]
