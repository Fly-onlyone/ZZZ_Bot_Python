---
tags: [frontend, components, layout]
---

# ThemePicker

> Palette icon button that opens a menu of the four theme presets and persists the choice.

## How it works
Renders a `PaletteIcon` `IconButton` that opens an MUI `Menu` with four entries — Nebula, Venom, Glacier, Cyber. Each entry shows a color swatch drawn from `THEME_COLORS[value].primary.main` ([[Theme Colors]]) plus a `CheckIcon` next to the active theme. Selecting an entry calls [[ThemeContext]] `changeTheme(name)` for immediate UI swap, then [[DataLoader]] `useSaveData("settings")` to persist `{...settings, theme: name}` to the backend. The button is disabled until `useBackendHealth().data.ready === true`, and the current `settings` payload is loaded via `useRouteData("settings", {enabled: isBackendReady, retry: 6, refetchOnWindowFocus: true})` so the spread on save doesn't blow away other fields.

## Source
- `frontend/src/components/layout/ThemePicker.jsx` — primary

## Depends on
- [[ThemeContext]] — `themeName`, `changeTheme`
- [[Theme Colors]] — swatch source
- [[DataLoader]] — health, route data, save mutation
- [[Theme Styles]] — `GLOW.border`

## Used by
- [[AppHeader]] — right-side controls

## Gotchas
- Disabled until backend reports ready, otherwise the persisted theme would clobber server defaults.

## See also
- [[_index]]
- [[AppHeader]]
- [[ThemeContext]]
- [[MUI Theme Factory]]
