---
tags: [architecture, flow]
---

# Sidecar Lifecycle

> The Tauri Rust shell owns the lifetime of the Python backend. It spawns the
> sidecar via `tauri_plugin_shell::sidecar()`, hands it a desktop token, monitors
> its health, and shuts it down via an escalating chain when the user quits.

## Source

- `src-tauri/src/lib.rs` — spawn + shutdown + escalation
- `backend/Bot.py` — receives `--hosted-by-tauri` and `ZZZ_DESKTOP_TOKEN`
- `frontend/scripts/prepare-tauri-sidecar.ts` — build-time binary rename

## How it works

```mermaid
stateDiagram-v2
    [*] --> ShellStart
    ShellStart --> Spawning: tauri_plugin_shell::sidecar()
    Spawning --> Ready: backend port responds to /health
    Ready --> Running: handler ticks + UI interaction
    Running --> GracefulShutdown: HTTP POST /shutdown (1s timeout)
    GracefulShutdown --> WaitExit: wait 2s
    WaitExit --> Exited: child terminated
    WaitExit --> ForceKill: still alive
    ForceKill --> Exited: kill() + wait 0.5s
    ForceKill --> Taskkill: still alive
    Taskkill --> Exited: taskkill /F /IM zzz-backend*
    Exited --> [*]
```

Desktop token (`zzz-desktop-{pid}-{nanos}`) is generated at shell startup, passed via
`ZZZ_DESKTOP_TOKEN` env var, and required on `/shutdown` and `/tasks/run-playwright`
requests so a stale browser tab can't kill the backend.

## Depends on

- [[Sidecar Spawn]] — the spawn call
- [[Sidecar Shutdown Escalation]] — the cleanup chain
- [[Desktop Token]] — identity validation
- [[Backend Port Resolution]] — `backend_port()` env-aware default
- [[PyInstaller Sidecar Build]] — what gets spawned
- [[Tauri]] — runtime

## Used by

- [[Daily Task Cycle]] — runs inside the spawned sidecar
- [[Tray Menu]] — "Exit" triggers shutdown

## Gotchas

- The taskkill fallback uses a wildcard (`zzz-backend*`) to catch any binary naming variant — but it'll also kill unrelated processes starting with `zzz-backend` if any exist.
- Sidecar binary is renamed to `zzz-backend-{target-triple}.exe` at build time; Tauri looks up that exact name. See [[Prepare Tauri Sidecar Script]].

## See also

- [[_index]]
- [[Sidecar Shutdown Escalation]]
- [[Desktop Token]]
- [[Tauri]]
