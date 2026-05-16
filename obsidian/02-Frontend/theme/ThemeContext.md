---
tags: [frontend, theme]
---

# ThemeContext

> Provider that owns `themeName`, derived `themeColors`, and the user's `prefers-reduced-motion` flag — syncing the theme from backend settings.

## Source
- `frontend/src/theme/ThemeContext.jsx` — primary

## How it works
1. `useReducedMotionPreference` subscribes to `(prefers-reduced-motion: reduce)` and updates on `change`.
2. `ThemeContextProvider` initializes state at `nebula`, then waits for backend readiness via `useBackendHealth().data?.ready` from [[DataLoader]].
3. Once ready, it fetches `useRouteData("settings", { enabled, retry: 6, exponential backoff to 3s })` and writes `settingsData.theme` into both `themeName` and `themeColors` (via [[Theme Colors]] `getThemeColors`).
4. Exposes `changeTheme(name)` for the [[ThemePicker]] and the full context to consumers via `useThemeContext()`.

## Depends on
- [[Theme Colors]] — `getThemeColors`
- [[DataLoader]] — health probe + settings fetch
- [[Settings Endpoints]] — backend `theme` field

## Used by
- [[MUI Theme Factory]] — receives `themeName` + `themeColors`
- [[ThemePicker]] — calls `changeTheme`
- [[PermanentDrawer Router]] and most pages — for accent glow + reduced-motion checks

## Gotchas
- Settings fetch is gated on health; before backend is ready the UI renders with the nebula default.

## See also
- [[_index]]
- [[Theme Colors]]
- [[Settings Persistence Flow]]
