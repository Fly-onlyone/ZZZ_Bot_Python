---
tags: [frontend, hooks]
---

# useFieldRenderer

> Maps a field key/value to the right input component, auto-detecting booleans, arrays, selects, and password fields.

## Source
- `frontend/src/hooks/useFieldRenderer.jsx` — primary

## How it works
The hook accepts an optional `typeConfig` and returns `{ renderField, isPasswordField }`. `renderField(key, value, onChange)` dispatches by precedence:

1. `typeConfig[key].type === "select"` with options → [[Select Field]].
2. `Array.isArray(value)` → [[Array Field]] (e.g. schedule time pickers).
3. `typeof value === "boolean"` → [[Boolean Field]] (Switch).
4. Default → [[Text Field]] with `isPassword` set when the key matches any keyword in `PASSWORD_FIELD_KEYWORDS` from [[Frontend Constants]] (case-insensitive `includes`).

Implements [[Dynamic Form ValueAdapter Pattern]].

## Depends on
- [[Frontend Constants]] — `PASSWORD_FIELD_KEYWORDS`
- [[Text Field]], [[Boolean Field]], [[Select Field]], [[Array Field]] — leaf components

## Used by
- [[ValueAdapter]] — the dynamic form renderer
- [[Account Page]], [[Settings Page]] — via ValueAdapter

## See also
- [[_index]]
- [[useFormState]]
- [[Dynamic Form ValueAdapter Pattern]]
