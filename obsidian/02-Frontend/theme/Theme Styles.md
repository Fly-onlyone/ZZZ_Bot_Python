---
tags: [frontend, theme]
---

# Theme Styles

> Shared transition presets and a luminous `GLOW` shadow factory parameterized by theme accent color.

## Source
- `frontend/src/theme/styles.js` — primary

## How it works
- `TRANSITIONS` — three presets:
  - `default: "all 0.3s ease-in-out"`
  - `fast: "all 0.2s ease-in-out"`
  - `cubic: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"` (the workhorse used by the MUI factory).
- `GLOW` — factory functions taking a color hex; return layered `box-shadow` strings:
  - `subtle(color)` — base button shadow
  - `medium(color)` — hover state
  - `strong(color)` — emphasis / focused cards
  - `border(color)` — input border ring
  - `text(color)` — text drop glow

Colors are concatenated with hex alpha bytes (e.g. `${color}30`), assuming 6-digit hex inputs.

## Used by
- [[MUI Theme Factory]] — buttons, drawer, app bar
- Component sx props across [[SectionCard]], [[SaveStatus]], and various page surfaces

## Gotchas
- Pass 6-digit hex to `GLOW` helpers; shorthand (`#abc`) breaks the alpha-byte concatenation.

## See also
- [[_index]]
- [[MUI Theme Factory]]
- [[Aurora Tab Styles]]
