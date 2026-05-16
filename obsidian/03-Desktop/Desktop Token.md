---
tags: [desktop]
---

# Desktop Token

> Per-session shared secret in the form `zzz-desktop-{pid}-{nanos}` that proves a backend request came from the Tauri shell, not a stray browser tab.

## Source
- `src-tauri/src/lib.rs` — `generate_desktop_token()`, used in `setup`, `trigger_playwright_run()`, `stop_backend_sidecar()`

## How it works
Format: `zzz-desktop-{process_id}-{unix_nanos}`. Generated in `setup` (or read from existing `ZZZ_DESKTOP_TOKEN` env so the value is stable across re-entries).

1. Shell stores the token in `AppRuntime.desktop_token`.
2. Sidecar is spawned with `ZZZ_DESKTOP_TOKEN` env so the Python backend has the same value.
3. Privileged endpoints — `POST /shutdown`, `POST /tasks/run-playwright` — require the `x-desktop-token` header to match.

Per-PID + nanos means a relaunch produces a new token (unless inherited via env), so an orphaned tab from a previous session can't drive the new shell's backend.

## Depends on
- [[Sidecar Spawn]] — sets the env on the child
- [[System Endpoints]] — validates the header

## Used by
- [[Sidecar Shutdown Escalation]] — `/shutdown` POST
- [[Tray Menu]] — Run Playwright POST

## See also
- [[_index]]
- [[Tauri Shell Entry]]
