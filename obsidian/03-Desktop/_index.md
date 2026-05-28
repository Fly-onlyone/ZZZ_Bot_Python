---
tags: [moc, desktop]
---

# Desktop — Map of Content

> Tauri 2 Rust shell that wraps the Python sidecar + frontend WebView. Manages
> tray icon, window geometry, autostart, graceful shutdown, and the PyInstaller →
> NSIS bundle pipeline.

## Shell runtime

- [[Tauri Shell Entry]] — main.rs + lib.rs structure
- [[Tray Menu]] — system tray menu items (Run Playwright, Show Window, Exit After Run, Exit)
- [[Window State Dual Storage]] — backend settings + local `window-state.json` merge

## Sidecar lifecycle

- [[Sidecar Spawn]] — `tauri_plugin_shell::sidecar()` invocation with desktop token
- [[Sidecar Shutdown Escalation]] — HTTP shutdown → wait → kill → taskkill fallback
- [[Desktop Token]] — `zzz-desktop-{pid}-{nanos}` for sidecar identity validation
- [[Backend Port Resolution]] — `backend_port()` reads `ZZZ_DEV_BACKEND_PORT`, defaults 8000

## OS integration

- [[Autostart Reconciliation]] — syncs `autostart_on_login` with OS registry (20 retries)
- [[Single Instance Guard]] — second launches focus the running window instead of spawning a duplicate shell + sidecar

## Build pipeline

- [[PyInstaller Sidecar Build]] — `product/BotSidecar.spec`: hidden imports, data files, OpenSSL DLLs
- [[Prepare Tauri Sidecar Script]] — renames `zzz-backend.exe` → `zzz-backend-{target-triple}.exe`
- [[NSIS Installer Config]] — custom hooks; installs to `%LOCALAPPDATA%\Programs\ZZZ Bot`

## See also

- [[_HOME]]
- [[Sidecar Lifecycle]]
- [[Production Build Pipeline]]
- [[Tauri]]
- [[PyInstaller]]
- [[NSIS]]
