---
tags: [frontend, components, fields]
---

# Select Field

> MUI Select dropdown with theme-aware styling and a motion-driven entry.

## How it works
Receives `value`, `options` (`{value, label}[]`), and `onChange`. Renders a full-width MUI `FormControl` + `Select`, falling back to the first option's value if `value` is empty. Wrapped in a `motion.div` that slides in from the left on mount. Used by [[useFieldRenderer]] when a `typeConfig[fieldKey]` entry specifies `type: "select"` with an `options` array — for example the `theme` field in [[Settings Page]].

## Source
- `frontend/src/components/fields/SelectField.jsx` — primary

## Depends on
- [[ThemeContext]] — themeColors (currently destructured for future styling hooks)
- [[Framer Motion]] — entry variants
- [[MUI]] — `Select`, `MenuItem`, `FormControl`

## Used by
- [[ValueAdapter]] — via [[useFieldRenderer]]
- [[Settings Page]] — theme selector
- [[ThemePicker]] — pattern reference only

## See also
- [[_index]]
- [[Text Field]]
- [[Boolean Field]]
