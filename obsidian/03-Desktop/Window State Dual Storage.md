---
tags: [desktop]
---

# Window State Dual Storage

> Window geometry (position, size, maximized, minimized) persisted to BOTH the backend settings JSON and a local `window-state.json` so restore survives backend outages.

## Source
- `src-tauri/src/lib.rs` — `persist_window_size/position/flag`, `read_local_window_state`, `merge_window_state`, `resolved_window_state_for_restore`

## How it works
Six keys (`window_x`, `window_y`, `window_width`, `window_height`, `window_maximized`, `window_minimized`) are mirrored to two stores:

1. **Backend settings** via `POST /settings` (canonical, syncs with UI).
2. **Local `window-state.json`** in the app config dir (`app_config_dir()/window-state.json`) — pretty-printed JSON.

On restore, `resolved_window_state_for_restore()` merges both with **local overrides winning** for the six window keys. Off-screen positions are detected via `saved_window_rect_intersects_any_monitor()` and the window is centered instead. Persistence is debounced 500 ms (`WINDOW_STATE_PERSIST_DEBOUNCE_MS`) on move/resize; focus events flush display flags immediately. Maximized windows skip geometry persistence.

## Depends on
- [[Settings Endpoints]] — backend half of the mirror
- [[Settings Contract]] — defines window_* keys

## Used by
- [[Tauri Shell Entry]] — restored on startup, persisted on every move/resize/focus/close

## Gotchas
- Local file overrides backend on restore — useful when sidecar hasn't started, but means manual edits to backend settings JSON may not stick on next launch.

## See also
- [[_index]]
- [[Tauri Shell Entry]]
