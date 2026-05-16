---
tags: [moc, backend, api]
---

# Backend / api — Map of Content

> 35+ FastAPI endpoints in a single `routes.py` file, grouped by feature. The frontend
> uses `DataLoader` (TanStack Query) to call them; the Tauri shell calls a small
> shutdown/settings subset.

## Endpoint groups

- [[Health Endpoints]] — `/health`, `/check-run-status`, `/playstate`, `/logs`, `/events`
- [[Shopping Endpoints]] — `/shopping` GET/POST, `/overview/hunt`
- [[Redeem Endpoints]] — `/redeem` GET/POST
- [[Mission Endpoints]] — `/overview/mission`
- [[Account Endpoints]] — `/account` GET/POST, `/manual` POST
- [[Settings Endpoints]] — `/settings`, `/settings/advanced`
- [[Locator Tracker Endpoints]] — `/locator-tracker`, `/locator-tracker/failures`, `/locator-tracker/clear`
- [[Automation Endpoints]] — `/tasks/run-playwright` (desktop-token gated)
- [[Maintenance Endpoints]] — `/maintenance/legacy-migration`, `/maintenance/local-cleanup`
- [[System Endpoints]] — `/shutdown`, `/routes`
- [[Backup Endpoints]] — `/backup/summary,config,export,import,browse`
- [[Asset Endpoints]] — `/assets/screenshot/{filename}`

## See also

- [[_HOME]]
- [[01-Backend/_index|Backend]]
- [[Frontend Data Flow]]
- [[DataLoader]]
- [[FastAPI]]
