---
tags: [frontend, components, common]
---

# SectionCard

> Glassmorphic content card with a glowing icon badge header and themed gradients.

## Source
- `frontend/src/components/common/SectionCard.jsx` — primary

## How it works
Wraps `children` in an MUI `Paper` rendered as `motion.div` (entry: fade + slide-up, hover: lift + scale). The header strip uses `themeColors.gradients.header` and shows a memoized `IconBadge` whose spring-animated icon sits on a `gradients.primary` or `primaryLight` square (`colorScheme` prop). Border, glow, and background pull from [[ThemeContext]] (`themeColors.alpha.cardBorder`, `gradients.backgroundSubtle`, [[Theme Styles]] `GLOW.medium`). `disableHover` opts out of the lift, `sx` / `contentSx` extend the outer paper and inner padding. Title text uses Outfit with a glow text-shadow.

## Depends on
- [[ThemeContext]] — themeColors source
- [[Theme Styles]] — GLOW helpers
- [[Color Re-exports]] — `COMMON_COLORS.text.primary`
- [[Framer Motion]] — entry, hover, icon variants
- [[MUI Animation Component Prop Pattern]] — `component={motion.div}`

## Used by
- [[Mission Section]], [[Hunt Section]], [[Running Status Section]] — primary section wrapper
- [[Shopping Page]], [[Redeem Page]], [[Settings Page]], [[Account Page]], [[Backup Page]] — page-level cards

## See also
- [[_index]]
- [[EmptyState]]
- [[DataTable]]
