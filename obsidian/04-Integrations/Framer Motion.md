---
tags: [integration]
---

# Framer Motion

> Animation library used for page transitions, staggered list reveals, and the [[AuroraBackground]] gradient motion.

## Used for
- Page/section enter animations (`motion.div` variants)
- Staggered card reveals on Overview / Shopping / Redeem
- `AnimatePresence` for conditional rendering (`mode="wait"`)
- Aurora gradient panning in the themed background

## Configuration
- Version `framer-motion ^12.23.24` (`frontend/package.json`)
- Shared `containerVariants` / `itemVariants` in `frontend/src/content/`

## Wire-up
- Most page sections import from `framer-motion`
- MUI components opt-in via `component={motion.div}` rather than `motion(Paper)` wrapping

## Auth mode
N/A

## Gotchas
- Wrapping MUI components with `motion()` re-renders the entire MUI tree and breaks refs — always use the `component=` prop (see [[MUI Animation Component Prop Pattern]]).
- Prefer transform animations (`scale`, `x`, `y`) over `width` / `height` for GPU acceleration.

## See also
- [[_index]]
- [[MUI]]
- [[AuroraBackground]]
