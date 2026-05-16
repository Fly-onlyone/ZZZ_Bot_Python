---
tags: [moc, backend, core]
---

# Backend / core — Map of Content

> Application foundation: entry point, global state, constants, and the cross-cutting
> services every handler depends on.

## Entry & globals

- [[Bot Entry Point]] — Bot.py: scheduler, FastAPI lifecycle, playwright_task orchestrator
- [[GlobalVar]] — singleton state container (CONFIG paths, accounts, settings)
- [[Constants]] — image thresholds, timeouts, retention windows, HTTP pool sizes

## Cross-cutting services

- [[Notification Sender]] — Jinja2 mission emails with base64-embedded screenshots
- [[ManualLoginManager]] — SessionState machine for browser handoff UI
- [[Event Bus]] — thread-safe SSE broadcaster for real-time frontend updates
- [[Mission Email Scheduler]] — sync vs async email dispatch coordination
- [[Frontend Env Resolver]] — Sentry DSN resolution chain (Vite → env → settings)
- [[Settings Contract]] — advanced settings key whitelist extraction

## See also

- [[_HOME]]
- [[01-Backend/_index|Backend]]
- [[Daily Task Cycle]]
- [[Settings Persistence Flow]]
