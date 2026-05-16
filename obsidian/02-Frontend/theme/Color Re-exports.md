---
tags: [frontend, theme]
---

# Color Re-exports

> Backward-compatibility shim that re-exports theme constants under the old `COLORS`/`GRADIENTS`/`ALPHA` names.

## Source
- `frontend/src/theme/colors.js` — primary

## How it works
Pulls `THEME_COLORS`, `COMMON_COLORS`, and `getThemeColors` from [[Theme Colors]] and re-publishes them, plus three legacy aggregates pinned to the default nebula theme:

- `COLORS` — `{ primary, secondary, success, error, warning, info, text, background }` (theme primaries are static-nebula; semantic colors are common).
- `GRADIENTS` — `THEME_COLORS.nebula.gradients`.
- `ALPHA` — `THEME_COLORS.nebula.alpha`.

Also re-exports `THEME_COLORS`, `COMMON_COLORS`, and `getThemeColors` for code paths that already imported from `./colors`.

## Used by
- [[MUI Theme Factory]] — imports `COMMON_COLORS` here rather than directly from `themes.js`
- Older components still importing `COLORS`/`GRADIENTS`/`ALPHA`

## Gotchas
- `COLORS.primary`, `GRADIENTS`, and `ALPHA` are frozen to nebula — they don't follow the active theme. Use `useThemeContext().themeColors` for live values.

## See also
- [[_index]]
- [[Theme Colors]]
