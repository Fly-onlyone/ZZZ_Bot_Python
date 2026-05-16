---
tags: [backend, api]
---

# System Endpoints

> Process shutdown handshake for the Tauri shell and dynamic route discovery for the drawer.

## Source
- `backend/api/routes.py` — primary

## How it works
- `POST /shutdown` requires the `x-desktop-token` header. It accepts a JSON body with `source`, `run_event`, `reason`, `tracked_pid`, `shutdown_started_at` and normalizes it via `_build_shutdown_context()`. A daemon worker thread (`_start_shutdown_worker`) calls `_perform_desktop_shutdown()`, which opens a Sentry transaction, sleeps `SHUTDOWN_RESPONSE_DELAY_SECONDS` so the HTTP response can flush, flushes Sentry with a 2s timeout, then `os._exit(0)`. Response is `202 {"status": "accepted"}`. Called by [[Sidecar Shutdown Escalation]].
- `GET /routes` walks `app.routes`, filters out anything under `INTERNAL_ROUTE_PREFIXES` (docs, manual, images, screenshot, assets, playstate, logs, health, shutdown, tasks, maintenance, backup, events, locator-tracker), deduplicates, and returns the public list. Powers the dynamic frontend drawer.

## Depends on
- [[Desktop Token]] — `/shutdown` auth
- [[Sentry]] — shutdown trace + flush

## Used by
- [[Sidecar Shutdown Escalation]] — `/shutdown`
- [[PermanentDrawer Router]] — `/routes`

## See also
- [[_index]]
- [[Sidecar Lifecycle]]
