---
tags: [backend, api]
---

# Automation Endpoints

> Privileged manual-run trigger reserved for the Tauri shell.

## Source
- `backend/api/routes.py` — primary

## How it works
`POST /tasks/run-playwright` gates on `_has_valid_desktop_token(request)`, which compares the `x-desktop-token` header against the `ZZZ_DESKTOP_TOKEN` env var using `compare_digest`. When the token is missing or wrong it returns `401 {"status": "rejected"}`.

On accept, it resolves the live bot runtime module and calls `run_playwright_task_async(manual_run=True)`, which fires the full daily task pipeline in a background thread without waiting for the next scheduled tick.

This endpoint exists for the Tauri tray "Run Playwright" menu item — see [[Tray Menu]] and [[Desktop Token]]. The web UI does not call it because the token is only handed to the embedded WebView at sidecar spawn time.

## Depends on
- [[Desktop Token]] — auth gate
- [[Bot Entry Point]] — `run_playwright_task_async`

## Used by
- [[Tray Menu]] — "Run Playwright" item

## See also
- [[_index]]
- [[Sidecar Lifecycle]]
