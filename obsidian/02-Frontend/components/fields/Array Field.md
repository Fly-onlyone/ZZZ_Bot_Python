---
tags: [frontend, components, fields]
---

# Array Field

> Dynamic list of MUI time pickers used to manage `schedule_times`-style arrays.

## How it works
Renders one `TimePicker` per entry in `value` (an array of `"HH:mm"` strings). Each row wraps the picker plus a red gradient "Remove" button inside a framer `AnimatePresence` (mode `popLayout`) so add/remove animates with spring entry + shrink exit and `layout` reflow. A green "Add Time" button appends an empty string. Time values are parsed via `dayjs(time, "HH:mm")` and re-formatted on change. The success/error gradients use [[Color Re-exports]] (`COMMON_COLORS.success`, `COMMON_COLORS.error`) and [[Theme Styles]] `GLOW.subtle/medium`.

## Source
- `frontend/src/components/fields/ArrayField.jsx` — primary

## Depends on
- [[Day.js]] — time parsing/formatting
- [[MUI]] — `@mui/x-date-pickers` TimePicker (requires `LocalizationProvider` from [[Frontend Entry Point]])
- [[Framer Motion]] — `AnimatePresence` with `popLayout`
- [[ThemeContext]] — alpha tokens

## Used by
- [[ValueAdapter]] — via [[useFieldRenderer]] when value is an array
- [[Settings Page]] — `schedule_times`

## See also
- [[_index]]
- [[Settings Contract]]
- [[Frontend Entry Point]]
