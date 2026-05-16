---
tags: [frontend, components, fields]
---

# Boolean Field

> Themed MUI Switch wrapped in a motion container for boolean form values.

## How it works
Renders a single MUI `Switch` (checked = `value`) inside a `motion.div` that animates entry (opacity + scale spring), hover (scale 1.1), and tap (scale 0.95). Style overrides paint the checked thumb and track with `themeColors.secondary.main` from [[ThemeContext]] so the control re-themes when the user switches palettes. Change events forward `e.target.checked` through `onChange`. Layout uses `ml-auto` so the switch sits flush with the right edge of its parent row.

## Source
- `frontend/src/components/fields/BooleanField.jsx` — primary

## Depends on
- [[ThemeContext]] — secondary color
- [[Framer Motion]] — switch variants

## Used by
- [[ValueAdapter]] — via [[useFieldRenderer]] for boolean keys
- [[Settings Page]] — toggles such as `hide_browser`, `exit_after_run`, `enable_hunt_mode`

## See also
- [[_index]]
- [[Text Field]]
- [[Settings Contract]]
