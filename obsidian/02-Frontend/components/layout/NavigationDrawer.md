---
tags: [frontend, components, layout]
---

# NavigationDrawer

> Permanent (desktop) / temporary (mobile) side nav with hover-prefetch of route data.

## How it works
Memoized component that ships a fixed `tabs` array — Overview, Shopping, Account, Settings, Tools — each linking to its `path`. Width is fixed at `DRAWER_WIDTH` (240) from [[Frontend Constants]]. On hover or focus of any nav button, `handlePrefetch` looks up `PREFETCH_ROUTES_BY_PATH` and calls [[DataLoader]]'s `prefetchRoutes` so the destination page's TanStack Query cache is warmed before the click. Active state is computed from `useLocation().pathname` and drives row gradient, left border, glow shadow, icon scale, and a continuously-animating drop-shadow pulse. Framer `listItemVariants` stagger rows in by 100ms on mount. `isMobile` swaps the permanent `Drawer` for a `temporary` variant controlled by `open` / `onClose`.

## Source
- `frontend/src/components/layout/NavigationDrawer.jsx` — primary

## Depends on
- [[React Router]] — `useLocation`, `useNavigate`
- [[DataLoader]] — `prefetchRoutes`
- [[Frontend Constants]] — `DRAWER_WIDTH`
- [[ThemeContext]], [[Theme Styles]], [[Color Re-exports]]
- [[Framer Motion]]

## Used by
- [[PermanentDrawer Router]] — both desktop and mobile mount points

## See also
- [[_index]]
- [[AppHeader]]
- [[PermanentDrawer Router]]
