---
tags: [frontend, components, common]
---

# AuroraBackground

> Full-screen animated radial-gradient backdrop that shifts to match the active theme.

## How it works
Renders a fixed-position aria-hidden div at `zIndex: 0` with a base linear gradient drawn from `themeColors.aurora[0]` and `aurora[2]`. Inside it, four absolutely-positioned blurred radial-gradient "blobs" (each `borderRadius: 50%`, `filter: blur(40-50px)`) drift via inline-injected `auroraShift1/2/3` keyframes — translate + scale loops at 12s/15s/18s, with the fourth blob reversing `auroraShift1` over 20s. Animations are disabled when [[ThemeContext]] reports `prefersReducedMotion`. `pointerEvents: none` ensures it never intercepts clicks. Memoized to avoid re-rendering on every state change.

## Source
- `frontend/src/components/common/AuroraBackground.jsx` — primary

## Depends on
- [[ThemeContext]] — `themeColors.aurora` palette + reduced-motion flag
- [[Theme Colors]] — per-theme aurora arrays

## Used by
- [[PermanentDrawer Router]] — mounted once as the app backdrop

## See also
- [[_index]]
- [[Aurora Tab Styles]]
- [[Theme Colors]]
