---
tags: [backend, api]
---

# Backup Endpoints

> Serialize, restore, and browse-pick backup files for all registered SQLite tables.

## Source
- `backend/api/routes.py` — primary

## How it works
- `GET /backup/summary` returns per-collection metadata (row counts, last update) via `DataStore.get_data_summary()`.
- `GET /backup/config` / `POST /backup/config` read and write the backup config row (export folder path, etc.).
- `POST /backup/browse` opens a native Tk folder picker (`tk.Tk().withdraw()` + `filedialog.askdirectory` with `-topmost`) and returns the chosen path or `{cancelled: true}`. Initial dir is the previously configured export path.
- `POST /backup/export` writes a timestamped `zzz-bot-backup-<ts>.json` file to the configured export folder, populated by `DataStore.export_all_data()`.
- `POST /backup/import` accepts `{data, collections}`, calls `DataStore.import_data()` for the selected subset, then invokes `_refresh_runtime_state_after_restore()` so live settings, accounts, and schedulers are all reconciled.

All collection coverage is driven by `_SINGLE_DOC_COLLECTIONS` / `_MULTI_DOC_COLLECTIONS` — adding a new collection requires updating those sets (see [[Backup Collection Registration Pattern]]).

## Depends on
- [[DataStore]] — export/import + collection sets

## Used by
- [[Backup Page]] — full UI

## See also
- [[_index]]
- [[Data Backup and Restore]]
