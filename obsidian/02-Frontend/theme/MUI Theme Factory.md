---
tags: [frontend, theme]
---

# MUI Theme Factory

> Builds a complete MUI theme — palette, typography, and glow-styled component overrides — from a theme name and color palette.

## Source
- `frontend/src/theme/muiTheme.js` — primary

## How it works
`createMuiTheme(themeName, prefersDarkMode, themeColors)` returns `createTheme({ palette, components, typography, shape })`:

- **Palette** — delegated to `createThemePalette` from [[Theme Colors]].
- **Component overrides** (`createComponentOverrides`) — wires the active `themeColors.glow` + `alpha` into:
  - `MuiOutlinedInput`/`MuiSelect`/`MuiInputLabel` — hover/focus glow rings.
  - `MuiCssBaseline` — slim 8px scrollbar, `overflowX: hidden`.
  - `MuiDrawer` — gradient backdrop, blurred glass, right-edge luminous strip pseudo-element.
  - `MuiAppBar` — translucent backdrop blur with bottom glow strip.
  - `MuiButton` — rounded 12px, lifts on hover, uses `GLOW.subtle/medium` from [[Theme Styles]].
  - `MuiPaper` (menu variant), `MuiDataGrid`, `MuiListItem`, `MuiListItemButton` — accent borders + hover backgrounds.
- **Typography** — Inter body, Outfit headings/buttons.
- **Shape** — global `borderRadius: 12`.

## Depends on
- [[Theme Colors]] — palette + `themeColors`
- [[Theme Styles]] — `GLOW`, `TRANSITIONS`
- [[MUI]] — `createTheme`

## Used by
- [[Frontend Entry Point]] — wraps the app in `<ThemeProvider>` with the result

## See also
- [[_index]]
- [[ThemeContext]]
- [[MUI Animation Component Prop Pattern]]
