---
tags: [integration]
---

# NSIS

> Nullsoft Scriptable Install System — the Windows installer technology Tauri uses to produce the `.exe` shipped to users.

## Used for
- Producing the user-facing `ZZZ Bot Setup *.exe` installer
- Per-user install under `%LOCALAPPDATA%\Programs\ZZZ Bot` (no UAC prompt)
- Pre-install hook to override the default install dir

## Configuration
- Configured in `src-tauri/tauri.conf.json` → `bundle.windows.nsis`:
  - `installMode: "currentUser"`
  - `installerHooks: "./windows/hooks.nsh"`
- `src-tauri/windows/hooks.nsh` — defines `NSIS_HOOK_PREINSTALL` to set `$INSTDIR` to `$LOCALAPPDATA\Programs\ZZZ Bot`
- Bundled artifacts: `mainBinaryName` + `externalBin: ["binaries/zzz-backend"]`

## Wire-up
- `src-tauri/tauri.conf.json` — NSIS bundle config
- `src-tauri/windows/hooks.nsh` — pre-install macro
- `cargo tauri build` — invokes the bundler

## Auth mode
N/A

## Gotchas
- `currentUser` install means no admin rights needed, but also means no `HKLM` registry entries — autostart uses `HKCU\...\Run` via the `tauri-plugin-autostart` crate (see [[Autostart Reconciliation]]).

## See also
- [[_index]]
- [[NSIS Installer Config]]
- [[Tauri]]
