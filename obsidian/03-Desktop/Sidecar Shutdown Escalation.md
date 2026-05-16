---
tags: [desktop]
---

# Sidecar Shutdown Escalation

> Three-tier shutdown ladder: graceful HTTP POST, then tracked-child kill, then Windows `taskkill` wildcard fallback.

## Source
- `src-tauri/src/lib.rs` — `stop_backend_sidecar()`, `wait_for_backend_termination()`, `force_kill_backend_processes()`, `determine_shutdown_escalation()`

## How it works
Triggered by tray Exit, window close, or run-event `Exit`/`ExitRequested`. Guarded by `shutdown_in_progress` flag so it runs once.

1. **Graceful (1 s HTTP)** — `POST /shutdown` with `x-desktop-token` and a JSON payload (source, run_event, reason, tracked_pid, shutdown_started_at).
2. **Wait 2 s** (`BACKEND_SHUTDOWN_GRACEFUL_WAIT_MS`, polled every 100 ms) for the sidecar to mark itself terminated.
3. **Direct kill** — if still alive, `child.kill()` on the tracked `CommandChild`, then wait 500 ms.
4. **Force `taskkill`** — `/F /T /PID {pid}`, then `/F /T /IM` for known image names (`zzz-backend.exe`, target-triple variants), finally `/F /T /FI "IMAGENAME eq zzz-backend*" /IM *` wildcard. All run with `CREATE_NO_WINDOW` so no console flashes.

## Depends on
- [[Sidecar Spawn]] — provides the tracked `CommandChild`
- [[Desktop Token]] — auth on `/shutdown`
- [[System Endpoints]] — `/shutdown` route

## Used by
- [[Tray Menu]] — Exit menu
- [[Tauri Shell Entry]] — close + exit events

## See also
- [[_index]]
- [[Sidecar Lifecycle]]
