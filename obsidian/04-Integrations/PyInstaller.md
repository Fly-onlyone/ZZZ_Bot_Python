---
tags: [integration]
---

# PyInstaller

> Bundles the Python backend (FastAPI, Playwright, OpenCV, scheduler) into a single `zzz-backend.exe` that Tauri ships as a sidecar.

## Used for
- Producing the sidecar binary consumed by [[Sidecar Spawn]]
- Bundling templates, sample images, Playwright Firefox, and apprise plugins

## Configuration
- Version `pyinstaller==6.16.0` + `pyinstaller-hooks-contrib==2025.9` (dev group)
- Spec: `product/BotSidecar.spec` (see [[PyInstaller Sidecar Build]])
- Output: `product/dist/zzz-backend.exe`
- Single-file `EXE`, `console=false`, UPX-compressed, `optimize=1`

## Wire-up
- `product/BotSidecar.spec` — primary spec
- `frontend/scripts/prepare-tauri-sidecar.ts` — invokes via `uv run --group dev pyinstaller`

## Auth mode
N/A

## Gotchas
- Hidden-import detection misses `plyer.platforms.win.*`, `apprise.plugins.email.*`, and `tkinter` — all must be declared in the spec.
- NumPy 2.x DLLs (`numpy.libs`) and OpenSSL DLLs (`libssl-*.dll`, `libcrypto-*.dll`) must be hand-collected — auto-collection misses them on Windows.
- The MCP-related modules (`fastmcp`, `mcp`, `mcp_tools`, `sentry_sdk.integrations.mcp`) are explicitly excluded to keep the bundle small.

## See also
- [[_index]]
- [[PyInstaller Sidecar Build]]
- [[Sidecar Build]]
