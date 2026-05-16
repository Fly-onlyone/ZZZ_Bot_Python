---
tags: [frontend, components, common]
---

# DataTable

> Themed HTML table with motion-staggered row entry and configurable cell rendering.

## How it works
Memoized component that takes `columns` (`{key, label, width?}[]`), `data`, a `renderCell(row, key, index)` callback, and optional `getRowBackground` / `getRowHoverBackground` per-row styling hooks. The outer `Box` is styled as `table` with a header that uses `themeColors.gradients.header`; each `tbody` row is a `motion.tr` driven by `tableRowVariants` (50ms-staggered slide-in spring). Row backgrounds default to `themeColors.alpha.card` and `alpha.hover`; the last row drops its bottom border. Row keys prefer `row.id`, falling back to index.

> Despite the project's CLAUDE.md mentioning "MUI DataGrid", this is a plain motion-enhanced HTML table — not DataGrid.

## Source
- `frontend/src/components/common/DataTable.jsx` — primary

## Depends on
- [[ThemeContext]] — gradients and alpha tokens
- [[Color Re-exports]] — header text color
- [[Framer Motion]] — row entry stagger

## Used by
- [[Locator Tracker Page]] — telemetry table
- [[Mission Section]] — mission report rows

## See also
- [[_index]]
- [[SectionCard]]
