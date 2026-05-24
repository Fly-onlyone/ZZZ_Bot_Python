---
tags: [frontend, pages]
---

# Backup Page

> Four-card surface for inspecting the SQLite database state, exporting backups, restoring selectively, and running maintenance.

## How it works
Four [[SectionCard]] panels stacked with `cardVariants` stagger:

1. **Data Summary** — `backup/summary` lists every collection with a Has data / Empty chip.
2. **Export** — picks an output folder via `/backup/browse` (native dialog), saves to `backup/config`, then triggers `backup/export`.
3. **Restore** — reads a local `.json` (`version === 1` required), shows per-collection checkboxes, posts to `backup/import`.
4. **Maintenance** — two cards rendered from `MAINTENANCE_TASKS`, both calling
   [[Maintenance Endpoints]]:
   - **Migrate from MongoDB** (`maintenance/mongo-migration`) — runs the one-shot Mongo →
     SQLite copy (see [[Migrate Mongo To SQLite]]); the success toast summarises per-collection
     counts from `report.summary` (skipping zero-row categories). `formatMongoMigrationSummary`
     handles the `status: "no_source"` case ("MongoDB not reachable — nothing to migrate.").
   - **Local Cleanup** (`maintenance/local-cleanup`) — archives and purges local
     logs/screenshots; success toast lists deleted-file counts.

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
