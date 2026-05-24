---
tags: [moc, integrations]
---

# Integrations — Map of Content

> External systems the bot depends on. Grouped by role.

## Target system

- [[HoYoLab]] — the event website automated by Playwright

## Runtime libraries (Python)

- [[Playwright]] — browser automation (Firefox bundled in sidecar)
- [[OpenCV]] — template matching for UI state detection
- [[SQLite]] — embedded primary persistence (stdlib `sqlite3`)
- [[Schedule]] — cron-like scheduler
- [[Jinja2]] — email templates
- [[Apprise]] — multi-channel notification dispatch (SMTP)
- [[Sentry]] — error + performance tracing (backend + frontend)
- [[FastAPI]] — REST + SSE server
- [[Uvicorn]] — ASGI runner

## Desktop shell

- [[Tauri]] — Rust desktop shell + IPC
- [[NSIS]] — Windows installer
- [[PyInstaller]] — Python → single-file exe

## Frontend libraries

- [[React]] — UI runtime
- [[MUI]] — component library
- [[TanStack Query]] — server state cache
- [[Framer Motion]] — animation
- [[React Router]] — client-side routing
- [[DnD Kit]] — drag-and-drop primitives
- [[Day.js]] — date formatting (MUI X adapter)

## Build tooling

- [[Vite]] — frontend bundler
- [[Bun]] — JavaScript runtime + package manager
- [[uv]] — Python package + project manager

## See also

- [[_HOME]]
- [[Production Build Pipeline]]
