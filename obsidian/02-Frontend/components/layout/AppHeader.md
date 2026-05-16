---
tags: [frontend, components, layout]
---

# AppHeader

> Fixed top app bar with logo, title, theme picker, and a zoom-indicator chip.

## How it works
MUI `AppBar` pinned above the drawer (`zIndex: drawer + 1`). Layout uses absolute positioning: hamburger (mobile only) + animated 48px logo tile on the left, "ZZZ Bot" Outfit title centered, and a right cluster containing the optional `ZoomChip` and the [[ThemePicker]]. The logo tile uses a per-theme `iconGlow` keyframes pulse driven by `themeColors.glow` via [[Theme Styles]] `GLOW.subtle/strong`, disabled when [[ThemeContext]] reports `prefersReducedMotion`. `ZoomChip` only renders when zoom is not 100% — clicking it pops a Popover with a "Restore to 100%" button that calls [[useZoom]]'s `resetZoom`. `onMenuClick` opens the mobile nav drawer.

## Source
- `frontend/src/components/layout/AppHeader.jsx` — primary

## Depends on
- [[ThemeContext]] — glow + reduced motion
- [[Theme Styles]] — `GLOW`, `TRANSITIONS`
- [[useZoom]] — zoom level + reset
- [[ThemePicker]] — palette switcher

## Used by
- [[PermanentDrawer Router]] — mounted once at top of layout

## See also
- [[_index]]
- [[NavigationDrawer]]
- [[ThemePicker]]
