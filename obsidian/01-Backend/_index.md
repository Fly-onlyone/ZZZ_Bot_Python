---
tags: [moc, backend]
---

# Backend — Map of Content

> Python FastAPI server + Playwright browser automation + OpenCV image recognition.
> Runs as a CLI in dev (`uv run python backend/Bot.py`) or as a Tauri-managed sidecar
> in production. Default dev port **8001**, production port **8000**.

## Subzones

- [[01-Backend/core/_index|core]] — entry point, globals, notifications, manual login, SSE bus
- [[01-Backend/handlers/_index|handlers]] — Mission, Shopping, Draw, Hunt orchestrators
- [[01-Backend/automation/_index|automation]] — Playwright wrappers + OpenCV + locator tracking
- [[01-Backend/services/_index|services]] — browser session manager
- [[01-Backend/repositories/_index|repositories]] — MongoDB primary + legacy JSON
- [[01-Backend/domain/_index|domain]] — typed models, enums
- [[01-Backend/api/_index|api]] — 35+ FastAPI endpoints grouped by feature
- [[01-Backend/utils/_index|utils]] — data, logging, screenshots, notifications, migration
- [[01-Backend/strategies/_index|strategies]] — pluggable image comparison
- [[01-Backend/message/_index|message]] — Jinja2 email templates

## See also

- [[_HOME]]
- [[Daily Task Cycle]]
- [[02-Frontend/_index|Frontend]]
- [[03-Desktop/_index|Desktop]]
