---
tags: [operations]
---

# Output Files

> `output/` holds everything the user owns: settings, credentials, shopping lists, mission reports, last-run state — all resolved via `resource_path(..., outside_path=True)` so an exe upgrade doesn't wipe them.

## Source
- `output/` — runtime directory next to the exe (or at the repo root in dev)

## How it works
Typical contents:

- `settings.json` — schedule times, theme, hunt toggles ([[Settings Contract]]).
- `account.json` — Gmail credentials for notifications.
- `shopping.json` — `Selected`, `Hunt`, and `Item's list` payload.
- `missions.json` — historical mission reports (also mirrored to MongoDB).
- `last_run.json` — timestamp + summary of the most recent automation cycle.
- `authentication data/` — persisted Playwright [[Storage State Store]] for session reuse.
- `screenshot/` — locator-tracker screenshots ([[Screenshot Store]]).

Every file routes through [[Resource Path Resolution Pattern]] with `outside_path=True`. The Tauri installer creates the directory on first launch.

## Depends on
- [[Resource Path Resolution Pattern]]
- [[Serializable Data Pattern]]

## Used by
- [[Data Backup and Restore]]

## Gotchas
- Deleting `output/` resets all settings and forces a re-login.

## See also
- [[_index]]
- [[Logging Setup]]
