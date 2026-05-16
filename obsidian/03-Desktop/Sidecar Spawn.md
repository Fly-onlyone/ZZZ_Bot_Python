---
tags: [desktop]
---

# Sidecar Spawn

> Spawns the PyInstaller-built Python backend as a Tauri sidecar process during `setup`, passing the desktop token and Sentry DSN via env.

## Source
- `src-tauri/src/lib.rs` — `spawn_backend_sidecar()`, `resolve_sidecar_sentry_dsn()`
- `src-tauri/tauri.conf.json` — `externalBin: ["binaries/zzz-backend"]`

## How it works
Skipped under `debug_assertions` (dev mode runs the backend manually). Otherwise:

1. Builds a `tauri_plugin_shell::sidecar("zzz-backend")` command — Tauri resolves to the target-suffixed binary `zzz-backend-{target-triple}.exe`.
2. Args: `--port {backend_port}`, `--no-frontend`, `--hosted-by-tauri`.
3. Env: `ZZZ_DESKTOP_TOKEN` (always), `SENTRY_DSN` (if resolved from `SENTRY_DSN` env or build-time `ZZZ_SENTRY_DSN`).
4. Stores the `CommandChild` in `AppRuntime.backend_child` (mutex) so shutdown can kill it.
5. Async task drains `CommandEvent` stream; `Terminated` flips `backend_terminated = true`.

## Depends on
- [[Tauri]] — `tauri-plugin-shell` provides the sidecar API
- [[PyInstaller Sidecar Build]] — produces the binary
- [[Desktop Token]] — passed via env
- [[Backend Port Resolution]] — `--port` value

## Used by
- [[Sidecar Lifecycle]]
- [[Sidecar Shutdown Escalation]]

## See also
- [[_index]]
- [[Tauri Shell Entry]]
