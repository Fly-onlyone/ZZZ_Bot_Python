---
tags: [moc, operations]
---

# Operations — Map of Content

> Build, dev, release, debug. Everything you need to take ZZZ Bot from source to a
> signed NSIS installer.

## Dev workflow

- [[Dev Server Architecture]] — backend on 8001, Vite on 3000, dual-process model
- [[Bot Dev Run]] — `uv run python backend/Bot.py`
- [[Tauri Dev Run]] — `bun run tauri:app` orchestration
- [[SIMULATE_EXE Switch]] — env var to force exe-mode path resolution in dev

## Build & release

- [[Production Build Pipeline]] — full pipeline overview
- [[Sidecar Build]] — `pyinstaller product/BotSidecar.spec`
- [[NSIS Installer Build]] — `cargo tauri build`

## Configuration

- [[Port Configuration]] — dev/prod port split and how VITE_BACKEND_URL resolves
- [[Logging Setup]] — TimedRotatingFileHandler + NoImportFilter
- [[Output Files]] — settings.json, account.json, shopping.json, missions.json

## Data ops

- [[Data Backup and Restore]] — /backup/export and /backup/import flow

## Testing

- [[Test Suite]] — pytest under backend/test/

## See also

- [[_HOME]]
- [[03-Desktop/_index|Desktop]]
- [[Resource Path Resolution Pattern]]
