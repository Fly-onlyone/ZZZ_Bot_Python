---
tags: [pattern]
---

# Dynamic Form ValueAdapter Pattern

> Render a settings form by inspecting the value's runtime type and dispatching to the right MUI input.

## When to apply
Any settings / config screen whose schema comes from a backend JSON file you don't want to hand-mirror in React.

## The pattern
```jsx
// ValueAdapter.jsx (conceptual)
function ValueAdapter({ value, onChange, path }) {
  if (typeof value === "boolean") return <BooleanField ... />;
  if (Array.isArray(value))       return <ArrayField ... />;
  if (typeof value === "object")  return Object.keys(value).map(k => <ValueAdapter ... />);
  return <TextField ... />;
}
```

Boolean → `Switch`, array → repeatable input list, object → nested recursion, scalar → `TextField`.

## Why
The backend persists arbitrary JSON shapes. A type-driven adapter means adding a new setting in `settings.json` shows up in the UI with zero React changes — and the wire format never drifts from the form.

## Don't
- Don't add per-setting components above the adapter — that defeats the point.
- Don't mutate the value in place; pass deltas up through `onChange` so [[useFormState]] keeps a clean diff.
- Don't infer types from the field name — read the actual runtime type.

## See also
- [[_index]]
- [[ValueAdapter]]
- [[useFormState]]
- [[Settings Page]]
