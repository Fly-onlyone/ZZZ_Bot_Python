---
tags: [backend, utils]
---

# NotificationHelper

> Cross-platform desktop notifications: persistent winotify on Windows, plyer fallback everywhere else.

## Source
- `backend/utils/NotificationHelper.py` — primary

## How it works
At import time it detects platform. On Windows it tries `winotify`; if missing it logs a warning and falls back to `plyer`. On non-Windows it uses `plyer` directly.

`notify(title, message, app_icon=None, app_id="ZZZ Bot", duration="short", timeout=5)` is the single public function:

- `_send_windows_notification` builds a `WinNotification(app_id, title, msg, duration, icon)` and calls `set_audio(audio.Default, loop=False)`. The toast persists in Windows 10/11 Action Center under the given `app_id`. Icons must be absolute `.ico` paths — non-existent paths are logged and skipped.
- `_send_plyer_notification` calls `plyer_notification.notify(...)` with a timeout (non-persistent).

Any error is caught and printed to console so a notification failure never crashes a run.

The module also re-exports a `notification` object exposing `.notify()` for drop-in compatibility with code that used to import `from plyer import notification`.

## Depends on
- `winotify` — Windows toasts
- `plyer` — fallback

## Used by
- [[Bot Entry Point]] — startup + run-complete toasts
- [[NotificationHelper]] callers in handlers

## See also
- [[_index]]
- [[Notification Pipeline]]
