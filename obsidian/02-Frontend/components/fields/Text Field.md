---
tags: [frontend, components, fields]
---

# Text Field

> Themed MUI text input with optional password show/hide and copy-to-clipboard buttons.

## How it works
Wraps `MuiTextField` in a motion container (left-slide entry). When `isPassword` is true the input `type` toggles between `password` and `text` via an internal `passwordVisible` state and a `Visibility`/`VisibilityOff` icon button. A `ContentCopy` button always appears and writes `value` to `navigator.clipboard`. Both icon buttons use framer scale/rotate variants on hover/tap. Selection of `isPassword` happens upstream in [[useFieldRenderer]], which checks the field key against `PASSWORD_FIELD_KEYWORDS` (currently `["password"]`) from [[Frontend Constants]].

## Source
- `frontend/src/components/fields/TextField.jsx` — primary

## Depends on
- [[ThemeContext]] — hover colors
- [[Color Re-exports]], [[Theme Styles]] — `TRANSITIONS.default`
- [[Framer Motion]] — container + button variants
- [[useFieldRenderer]] — decides `isPassword` per key

## Used by
- [[ValueAdapter]] — via [[useFieldRenderer]]
- [[Account Page]], [[Settings Page]] — text + password fields

## Gotchas
- Clipboard write fails silently if the page lacks the permission.

## See also
- [[_index]]
- [[Boolean Field]]
- [[Select Field]]
- [[Array Field]]
