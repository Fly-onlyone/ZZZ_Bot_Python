---
tags: [desktop]
---

# Tray Menu

> Native system tray icon with four menu items that mirror and toggle key backend settings.

## Source
- `src-tauri/src/lib.rs` — `build_tray()`, `get_tray_settings()`, `toggle_backend_setting()`

## How it works
`build_tray()` reads `show_window_on_startup` and `exit_after_run` from the backend `/settings` endpoint to seed the two `CheckMenuItem` states. Items:

1. **Run Playwright** — POSTs to `/tasks/run-playwright` with the desktop token header.
2. **Show Window on Startup** — toggles backend setting and updates the check state.
3. **Exit After Run** — toggles backend setting and updates the check state.
4. **Exit** — calls `stop_backend_sidecar()` then `app.exit(0)`.

Left-click or double-click on the tray icon shows / unminimizes / focuses the main window. The menu is suppressed on left-click (`show_menu_on_left_click(false)`).

## Depends on
- [[Tauri Shell Entry]] — built during `setup`
- [[Settings Endpoints]] — read/write via HTTP
- [[Desktop Token]] — Run Playwright auth header

## Used by
- [[Sidecar Lifecycle]] — Exit triggers shutdown escalation

## See also
- [[_index]]
- [[Sidecar Shutdown Escalation]]
