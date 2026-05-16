---
tags: [pattern]
---

# MUI Animation Component Prop Pattern

> Animate MUI components via the `component={motion.div}` prop, never by wrapping them in `motion(Paper)`.

## When to apply
Any Framer Motion animation on a MUI element — entrance fades, hover scales, drag, layout animations.

## The pattern
```jsx
// Correct: keep MUI semantics, gain motion props
<Paper component={motion.div} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
  ...
</Paper>

<Button component={motion.button} whileTap={{ scale: 0.96 }}>
  Save
</Button>
```

For staggered lists, define `containerVariants` and `itemVariants` and apply them on the parent and children — see the `content/` sections.

## Why
`motion(Paper)` re-renders into a wrapping element, loses the MUI `sx` cascade context, and breaks `ref` forwarding for things like `Tooltip`. The `component=` prop swaps the underlying tag while keeping the MUI styling chain intact.

## Don't
- Don't call `motion(Paper)` — use `component={motion.div}`.
- Don't animate `width`/`height` — prefer transforms (`scale`, `x`, `y`) for performance.
- Don't forget `<AnimatePresence mode="wait">` for conditional swaps; otherwise exits don't run.

## See also
- [[_index]]
- [[Framer Motion]]
- [[MUI]]
- [[Mission Section]]
