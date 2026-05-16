---
tags: [frontend, theme]
---

# Theme Colors

> Four-theme palette source (Nebula, Venom, Glacier, Cyber) plus shared semantic colors and the `getThemeColors` factory.

## Source
- `frontend/src/theme/themes.js` — primary

## How it works
- `THEME_COLORS` — dict keyed by `nebula` (violet/fuchsia, default), `venom` (emerald/lime), `glacier` (sky/indigo), `cyber` (fuchsia/cyan). Each entry holds `primary`, `secondary`, `gradients` (primary/header/background/backgroundSubtle), `alpha` (card/cardBorder/hover/divider), `aurora` (4-color array for [[AuroraBackground]]), and a single `glow` accent.
- `COMMON_COLORS` — semantic palette shared across themes: `success`, `error`, `warning`, `info`, `text` (primary→muted ramp), `background` (dark/paper/slate).
- `getThemeColors(name)` — safe lookup, defaults to nebula.
- `createThemePalette(name, isDark)` — assembles an MUI palette object used by [[MUI Theme Factory]].

## Used by
- [[ThemeContext]] — runtime theme switching
- [[MUI Theme Factory]] — palette + component overrides
- [[Color Re-exports]] — backward-compat alias
- [[AuroraBackground]] — `aurora` color array

## See also
- [[_index]]
- [[ThemeContext]]
- [[MUI Theme Factory]]
