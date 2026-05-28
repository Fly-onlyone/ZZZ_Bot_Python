---
tags: [desktop]
---

# Single Instance Guard

> Ensures only one ZZZ Bot shell runs at a time. A second launch (e.g. double-clicking the shortcut again) focuses the already-running window instead of spawning a duplicate shell + sidecar.

## Source
- `src-tauri/src/lib.rs` — `tauri_plugin_single_instance::init(...)` registered in `run()`, callback delegates to `show_main_window()`
- `src-tauri/Cargo.toml` — `tauri-plugin-single-instance = "2"`

## How it works
The plugin is the **first** plugin registered on the `tauri::Builder` — before `shell`, `autostart`, and `log`. Ordering matters: `tauri-plugin-autostart` injects `--minimized` into argv, so single-instance must claim the launch first to see the raw arguments.

When a second process starts, the plugin detects the existing instance during plugin init, forwards the new process's `argv` / `cwd` to the running instance via the `init` callback, and exits the second process **before** its `setup()` runs. Because `setup()` never executes in the duplicate, [[Sidecar Spawn]] is skipped there — no second `zzz-backend.exe` and no port-8000 clash.

The callback always brings the running window to the foreground via `show_main_window()` (`unminimize()` → `show()` → `set_focus()`). It does **not** inspect argv for `--minimized`: a manual relaunch means "show me the app", and the `--minimized` autostart launch only ever fires as the *first* instance (so the callback never runs for it).

## Gotchas
- Behavior only manifests in a packaged/release build. Under `debug_assertions` the sidecar spawn is skipped anyway, so the duplicate-process symptom is release-only.
- No capabilities/permissions entry is needed — single-instance is a Rust-only plugin with no JS commands.

## Depends on
- [[Tauri]] — `tauri-plugin-single-instance` (`2`)

## Used by
- [[Tauri Shell Entry]] — registers the plugin first in `run()`

## See also
- [[_index]]
- [[Autostart Reconciliation]] — shares the `--minimized` argv interaction
- [[Sidecar Spawn]] — skipped in the duplicate process that exits early
