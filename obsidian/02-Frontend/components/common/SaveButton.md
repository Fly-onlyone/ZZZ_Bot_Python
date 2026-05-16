---
tags: [frontend, components, common]
---

# SaveButton

> Neon-glow save button with a pulsing border, hover lift, and snackbar feedback.

## How it works
The button is a motion-wrapped MUI `Button` with three layers of animation: framer `buttonVariants` (hover scale 1.05 / tap 0.95), a wiggling `SaveIcon` (`iconVariants`), and an MUI `keyframes` `neonPulse` that breathes the box-shadow at 3s intervals using `themeColors.glow`. Pulse is disabled when [[ThemeContext]] reports `prefersReducedMotion`. While `loading`, the button is disabled and shows a `CircularProgress`. Feedback flows through the `alert` / `setAlert` props — an MUI `Snackbar` + `Alert` at the bottom-center auto-hides after 3s and is reset via `setAlert({...alert, open:false})`.

## Source
- `frontend/src/components/common/SaveButton.jsx` — primary

## Depends on
- [[ThemeContext]] — glow color + reduced-motion flag
- [[Theme Styles]] — `GLOW.strong`
- [[Framer Motion]] — button + icon variants

## Used by
- [[ValueAdapter]] — every dynamic form ends with this button
- [[Locator Tracker Page]] — clear action confirmations

## See also
- [[_index]]
- [[ValueAdapter]]
