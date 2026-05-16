---
tags: [moc, frontend, components, fields]
---

# Frontend / components / fields — Map of Content

> Form field primitives. [[ValueAdapter]] + [[useFieldRenderer]] picks one of these
> based on the value's type detected from the backend JSON.

- [[Text Field]] — text input; auto-masks fields whose name contains "password"
- [[Boolean Field]] — checkbox or toggle switch
- [[Select Field]] — dropdown with options from typeConfig
- [[Array Field]] — list/array editor with add/remove buttons

## See also

- [[_HOME]]
- [[02-Frontend/components/_index|components]]
- [[ValueAdapter]]
- [[useFieldRenderer]]
- [[Dynamic Form ValueAdapter Pattern]]
