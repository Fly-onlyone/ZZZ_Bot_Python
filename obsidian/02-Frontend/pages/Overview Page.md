---
tags: [frontend, pages]
---

# Overview Page

> Landing dashboard that combines a compact run-status banner with today's mission report.

## Source
- `frontend/src/pages/Overview.jsx` — primary

## How it works
The Overview is the only non-lazy route — [[PermanentDrawer Router]] eager-loads it as the default landing surface. It renders [[Compact Running Status]] at the top (last/next run + hunt summary) followed by a [[SectionCard]] wrapping the [[Mission Section]] for today's check-in result and mission table.

The single mission card animates in with a [[Framer Motion]] `cardVariants` stagger (`y: 20 → 0`, `scale: 0.95 → 1`, cubic ease) using the `component={motion.div}` prop, in line with the [[MUI Animation Component Prop Pattern]].

## Depends on
- [[Compact Running Status]] — banner
- [[Mission Section]] — body
- [[SectionCard]] — container
- [[Framer Motion]] — animations

## Used by
- [[PermanentDrawer Router]] — default route

## See also
- [[_index]]
- [[Mission Endpoints]]
