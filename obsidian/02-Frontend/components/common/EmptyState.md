---
tags: [frontend, components, common]
---

# EmptyState

> Centered placeholder card with an animated icon, title, optional subtitle, and optional action button.

## How it works
Renders an MUI `Paper` (motion `containerVariants`: spring fade-scale) containing an optional spring-rotated icon badge, an Outfit-styled title, an optional muted subtitle (max-width 360px), and an optional outlined action button. All colors are pulled from [[ThemeContext]] (`gradients.backgroundSubtle`, `gradients.primary`, `alpha.cardBorder`, `glow`) so the placeholder matches the active theme palette. The button only renders when both `action` and `actionLabel` props are supplied.

## Source
- `frontend/src/components/common/EmptyState.jsx` — primary

## Depends on
- [[ThemeContext]] — themeColors
- [[Color Re-exports]] — text colors
- [[Framer Motion]] — container + icon variants

## Used by
- [[Overview Page]], [[Shopping Page]], [[Redeem Page]], [[Locator Tracker Page]] — empty list / no-data fallbacks

## See also
- [[_index]]
- [[SectionCard]]
- [[Skeleton Set]]
