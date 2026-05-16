---
tags: [desktop]
---

# NSIS Installer Config

> Per-user NSIS installer that ships the Tauri shell + sidecar binary, installing under `%LOCALAPPDATA%\Programs\ZZZ Bot` to avoid UAC elevation.

## Source
- `src-tauri/tauri.conf.json` — `bundle.targets: ["nsis"]`, `bundle.windows.nsis`
- `src-tauri/windows/hooks.nsh` — `NSIS_HOOK_PREINSTALL` macro

## How it works
**`tauri.conf.json` NSIS block:**
```json
"windows": {
  "nsis": {
    "installMode": "currentUser",
    "installerHooks": "./windows/hooks.nsh"
  }
}
```

`installMode: currentUser` means no UAC prompt; the installer can write anywhere the user can. The pre-install hook overrides the default install dir:

```nsis
!macro NSIS_HOOK_PREINSTALL
  StrCpy $INSTDIR "$LOCALAPPDATA\\Programs\\ZZZ Bot"
!macroend
```

**Bundled artifacts:** `mainBinaryName: "ZZZ Bot"`, `externalBin: ["binaries/zzz-backend"]` (Tauri resolves to the target-triple-suffixed file produced by the sidecar prep script). Icons: `32x32.png`, `128x128.png`, `128x128@2x.png`, `icon.png/icns/ico`.

**CSP:** allows `http://127.0.0.1:8000-8001`, `http://localhost:8000-8001`, and `https://*.ingest.us.sentry.io`.

## Depends on
- [[NSIS]] — Nullsoft installer
- [[Tauri]] — bundler
- [[Prepare Tauri Sidecar Script]] — populates `externalBin`

## Used by
- [[Production Build Pipeline]]
- [[NSIS Installer Build]]

## See also
- [[_index]]
- [[Sidecar Spawn]]
