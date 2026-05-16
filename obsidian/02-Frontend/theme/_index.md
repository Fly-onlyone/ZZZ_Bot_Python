---
tags: [moc, frontend, theme]
---

# Frontend / theme — Map of Content

> 4-theme system: Nebula (purple), Venom (green), Glacier (blue), Cyber (red).
> Persisted theme name lives in `settings.json`; the React side reads it via
> [[ThemeContext]] on mount and rebuilds the MUI theme on switch.

- [[Theme Colors]] — `THEME_COLORS` palette per theme + `COMMON_COLORS` semantic colors
- [[ThemeContext]] — provider + `useThemeContext` hook; reduced-motion detection
- [[MUI Theme Factory]] — `createMuiTheme()` with component overrides (glow styling)
- [[Theme Styles]] — TRANSITIONS + GLOW factory helpers
- [[Aurora Tab Styles]] — Aurora-styled MUI Tabs sx + Framer Motion panel variants
- [[Color Re-exports]] — backwards-compat re-exports of `colors.js`

## See also

- [[_HOME]]
- [[02-Frontend/_index|Frontend]]
- [[ThemePicker]]
- [[MUI]]
- [[Framer Motion]]
