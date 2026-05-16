---
tags: [integration]
---

# React

> UI library powering the frontend SPA; renders inside the Tauri WebView in production and inside Vite's dev server during development.

## Used for
- All frontend pages, components, and content sections
- Concurrent rendering for smooth Overview / DataGrid updates
- Error boundaries via [[ErrorFallback]]

## Configuration
- Version `react ^18.3.1` + `react-dom ^18.3.1` (`frontend/package.json`)
- Strict mode enabled in [[Frontend Entry Point]]

## Wire-up
- `frontend/src/main.jsx` — `createRoot()` and provider stack (Theme, QueryClient, Router, Sentry)
- All `.jsx` files in `frontend/src/`

## Auth mode
N/A

## Gotchas
- Tauri's WebView is Edge / WebView2 on Windows — pin polyfills accordingly when adding modern JS APIs.

## See also
- [[_index]]
- [[Vite]]
- [[Frontend Entry Point]]
