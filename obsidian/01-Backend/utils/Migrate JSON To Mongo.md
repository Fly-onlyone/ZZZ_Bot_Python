---
tags: [backend, utils]
---

# Migrate JSON To Mongo

> One-shot importer that pulls legacy local JSON files and binary artifacts into MongoDB collections.

## Source
- `backend/utils/migrate_json_to_mongo.py` — primary

## How it works
`migrate_if_needed(output_dir, storage_state_path, screenshot_dir)` walks a fixed `_ARTIFACT_SPECS` list (`settings`, `account`, `shopping`, `missions`, `redeem`, `last_run`) and migrates each via `_migrate_artifact()`. Behavior per artifact:

1. Resolve the source path across primary output dir + LOCALAPPDATA fallbacks + `ZZZ_LEGACY_OUTPUT_DIRS` env var.
2. Read + type-validate the JSON payload.
3. If the target collection is empty, write the data (multi-record specs save record-by-record and track partial failures).
4. If the collection already has data AND the spec has a `replace_checker` (settings = matches defaults, account = blank), the existing doc is overwritten anyway — preserves real user data while replacing template-default rows.

Binary assets handled separately: `_migrate_storage_state()` and `_migrate_screenshots()` upsert into `binary_assets` with SHA-256 checksums so unchanged files are skipped. `_backfill_settings()` removes deprecated fields and seeds Sentry DSNs from env vars.

Returns a structured migration report (counts before/after, per-artifact action, storage / screenshot reports) which is also attached to a Sentry span. Triggered manually via [[Maintenance Endpoints]].

## Depends on
- [[MongoRepository]] — save / get methods
- [[Mongo Connection]] — `binary_assets`
- [[Sentry]] — span + report data

## Used by
- [[Maintenance Endpoints]] — `/maintenance/legacy-migration`

## Gotchas
- Multi-record specs use `migrated_partial` action on per-record failures — the response status surfaces this as `completed_with_warnings`.

## See also
- [[_index]]
- [[Data Backup and Restore]]
