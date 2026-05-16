---
tags: [frontend, pages]
---

# Backup Page

> Four-card surface for inspecting MongoDB state, exporting backups, restoring selectively, and running maintenance.

## How it works
Four [[SectionCard]] panels stacked with `cardVariants` stagger:

1. **Data Summary** — `backup/summary` lists every collection with a Has data / Empty chip.
2. **Export** — picks an output folder via `/backup/browse` (native dialog), saves to `backup/config`, then triggers `backup/export`.
3. **Restore** — reads a local `.json` (`version === 1` required), shows per-collection checkboxes, posts to `backup/import`.
4. **Maintenance** — runs `maintenance/legacy-migration` (JSON → Mongo) and `maintenance/local-cleanup` (purge logs/screenshots) via [[Maintenance Endpoints]].

Filename is `Backup.jsx` despite the route concept name. Mutations go through [[DataLoader]] `useActionData`.

## Source
- `frontend/src/pages/Backup.jsx` — primary

## Depends on
- [[Backup Endpoints]] — export/import/summary/config/browse
- [[Maintenance Endpoints]] — migration + cleanup
- [[DataLoader]] — query + mutation

## Used by
- [[Tools Page]] — Backup tab

## See also
- [[_index]]
- [[Data Backup and Restore]]
