---
tags: [integration]
---

# MUI

> Material UI component library + MUI X (DataGrid, DatePickers) — provides every button, card, table, form field, and date picker in the UI.

## Used for
- All page chrome, forms, dialogs ([[SectionCard]], [[SaveStatus]], [[Text Field]], etc.)
- Mission report table via `@mui/x-data-grid` ([[DataTable]], [[Locator Tracker Page]])
- Date filtering via `@mui/x-date-pickers` with the [[Day.js]] adapter
- Theming via `createTheme` + `ThemeProvider` (see [[MUI Theme Factory]])

## Configuration
- `@mui/material ^6.1.8`, `@mui/icons-material ^6.1.8`
- `@mui/system ^7.3.7`
- `@mui/x-data-grid ^7.23.0`, `@mui/x-date-pickers ^7.22.3`
- Emotion engine: `@emotion/react ^11.13.5`, `@emotion/styled ^11.13.5`
- Custom theme system with 4 palettes: Nebula, Venom, Glacier, Cyber

## Wire-up
- `frontend/src/theme/MUI Theme Factory.js` — `createTheme()`
- `frontend/src/main.jsx` — `ThemeProvider` + `CssBaseline`
- Component imports throughout `frontend/src/`

## Auth mode
N/A

## Gotchas
- Never wrap MUI components with `motion()` — use the `component={motion.div}` prop instead (see [[MUI Animation Component Prop Pattern]]).

## See also
- [[_index]]
- [[Framer Motion]]
- [[Day.js]]
