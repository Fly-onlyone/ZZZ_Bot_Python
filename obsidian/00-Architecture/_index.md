---
tags: [moc, architecture]
---

# Architecture — Map of Content

> Cross-cutting flows that span multiple modules. Read these first to build the
> mental scaffolding every other note references.

## Top-level orchestration

- [[Daily Task Cycle]] — scheduler → playwright_task() → handlers → email
- [[Browser Session Lifecycle]] — persistent Playwright context across runs

## Per-feature flows

- [[Hunt Mode Lifecycle]] — timed item purchase with three-phase execution
- [[Manual Login Flow]] — SessionState machine for user-initiated browser login
- [[Settings Persistence Flow]] — settings.json + MongoDB hybrid + frontend sync

## Cross-cutting pipelines

- [[Image Recognition Pipeline]] — OpenCV template matching for UI state detection
- [[Locator Telemetry Pipeline]] — Playwright selector instrumentation → MongoDB
- [[Notification Pipeline]] — Jinja2 templates → SMTP/Apprise → frontend SSE

## Desktop integration

- [[Sidecar Lifecycle]] — Tauri spawn → port negotiation → graceful shutdown

## Frontend

- [[Frontend Data Flow]] — TanStack Query + DataLoader + Server-Sent Events

## See also

- [[_HOME]]
- [[01-Backend/_index|Backend]]
- [[02-Frontend/_index|Frontend]]
- [[03-Desktop/_index|Desktop]]
