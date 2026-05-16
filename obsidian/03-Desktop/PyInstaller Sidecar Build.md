---
tags: [desktop]
---

# PyInstaller Sidecar Build

> PyInstaller spec that bundles the Python backend, OpenSSL DLLs, NumPy native libs, Playwright Firefox, sample images, and email templates into a single `zzz-backend.exe`.

## Source
- `product/BotSidecar.spec` — primary

## How it works
**Hidden imports:** `plyer.*` (Windows notifications), `tkinter` + `_tkinter` (file dialog), all `apprise.plugins.email.*` submodules.

**Data files (bundled into the exe):**
- `images/`, `sample/`, `reward image/` — OpenCV reference templates
- `backend/message/` — Jinja2 email templates
- `backend/playwright-browsers/` — bundled Firefox
- `apprise` email plugin source, `numpy` data

**Binaries:**
- NumPy 2.x delvewheel libs (`numpy.libs` — OpenBLAS, MSVCP) via `collect_dynamic_libs` + `collect_delvewheel_libs_directory`
- OpenSSL DLLs (`libssl-*.dll`, `libcrypto-*.dll`) hand-collected from `sys.prefix` / `sys.base_prefix` / `sys.exec_prefix` (+`DLLs/`)

**Output:** single-file `zzz-backend.exe`, `console=false`, UPX-compressed, `optimize=1`, icon `images/Qingyi02.ico`. Excludes `fastmcp`, `mcp`, `mcp_tools`, and `sentry_sdk.integrations.mcp` to keep size down.

## Depends on
- [[PyInstaller]] — `6.16.0`, `optimize=1`
- [[uv]] — invokes pyinstaller via `uv run --group dev`
- [[Playwright]] — bundled Firefox under `backend/playwright-browsers/`

## Used by
- [[Prepare Tauri Sidecar Script]] — invokes this spec
- [[Sidecar Spawn]] — runs the produced binary

## See also
- [[_index]]
- [[Sidecar Build]]
