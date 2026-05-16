---
tags: [frontend, theme]
---

# Aurora Tab Styles

> Aurora-styled MUI `Tabs` sx factory plus Framer Motion variants for tab panel transitions.

## Source
- `frontend/src/theme/tabStyles.js` — primary

## How it works
- `getAuroraTabsStyles(themeColors)` — returns an sx object for `<Tabs>` that hides the default `MuiTabs-indicator` and uses a pseudo-element (`&::after`) on each `MuiTab-root` to draw a 3px rounded pill underline. The selected tab activates the underline with `themeColors.primary.main` background and a layered `boxShadow` built from `themeColors.glow`.
- `auroraPanelVariants` — directional Framer Motion variants. `initial`/`exit` translate `x: direction * ±20` with a slight scale (0.995) and opacity fade; `animate` is a spring (`stiffness: 140, damping: 22, mass: 0.9`).
- `reducedMotionPanelVariants` — opacity-only fallback (120ms in / 80ms out) for users with `prefers-reduced-motion`.

## Depends on
- [[Theme Colors]] — `themeColors` shape
- [[Framer Motion]] — variant consumers
- [[ThemeContext]] — provides `prefersReducedMotion` for variant selection

## Used by
- [[Shopping Page]], [[Settings Page]], [[Account Page]], [[Tools Page]] — tab navigation

## See also
- [[_index]]
- [[Theme Styles]]
- [[MUI Animation Component Prop Pattern]]
