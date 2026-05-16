---
tags: [frontend, entry]
---

# Global CSS

> Tailwind base layer plus app-wide keyframes, scrollbar styling, fonts, and an accessibility focus ring.

## How it works
Begins with `@tailwind base; components; utilities;` so utility classes are available everywhere. Declares seven custom keyframes — `fadeIn`, `slideIn`, `pulse`, `shimmer`, `float`, `pulse-glow`, `slide-up-fade` — used by ad-hoc CSS animations and by the `.shimmer` helper class. Customizes `::-webkit-scrollbar` (8px, slate `#0f172a` track, `#334155` thumb that brightens on hover). Sets `html/body/#root` to full height with `overflow: hidden` on body and `overflow-x: hidden` on root. Applies a global 0.5s `fadeIn` to `body`, sets Inter as the body font and Outfit for headings, and adds antialiasing hints. A `*:focus-visible` rule renders a 2px purple `#8b5cf6` outline with 2px offset for keyboard accessibility, and `button/a/input/select/textarea` get a default 0.3s cubic-bezier transition.

## Source
- `frontend/src/index.css` — primary

## Depends on
- [[Vite]] — Tailwind processed via PostCSS pipeline

## Used by
- [[Frontend Entry Point]] — `import "./index.css"`

## See also
- [[_index]]
- [[Frontend Entry Point]]
- [[Theme Styles]]
