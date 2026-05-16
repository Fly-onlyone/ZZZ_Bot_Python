---
tags: [desktop]
---

# Autostart Reconciliation

> Background thread that keeps the backend `autostart_on_login` setting and the OS registry autostart flag in sync, retrying for up to 10 s on startup.

## Source
- `src-tauri/src/lib.rs` — `reconcile_autostart_preference()`, `reconcile_autostart_preference_once()`, `determine_autostart_sync_action()`

## How it works
On startup spawns a thread that polls every 500 ms for up to 20 attempts (`AUTOSTART_RECONCILE_ATTEMPTS`). Each attempt reads `autostart_on_login` from the backend and `is_enabled()` from `tauri-plugin-autostart`, then picks one of four actions:

| Persisted | OS State | Action |
|-----------|----------|--------|
| `None` | any | `Persist(live)` — first-run migration captures whatever OS says |
| `Some(true)` | disabled | `Enable` — restore OS state from preference |
| `Some(false)` | enabled | `Disable` — restore OS state from preference |
| matches | matches | `None` — already in sync, stop |

The autostart plugin is configured with `args(["--minimized"])` so autostart launches keep the main window hidden (see `started_minimized()`).

## Depends on
- [[Tauri]] — `tauri-plugin-autostart`
- [[Settings Endpoints]] — reads/writes `autostart_on_login`

## Used by
- [[Tauri Shell Entry]] — called from `setup`

## See also
- [[_index]]
- [[Settings Contract]]
