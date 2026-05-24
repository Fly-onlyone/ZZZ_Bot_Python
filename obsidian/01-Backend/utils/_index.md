---
tags: [moc, backend, utils]
---

# Backend / utils — Map of Content

> Reusable helpers. Functional, not class-oriented; safe to import from anywhere.

- [[DataHandler]] — Serializable JSON mixin; mission data prep + upsert orchestration
- [[NotificationHelper]] — cross-platform desktop notifications (winotify / plyer)
- [[StringUtil]] — number/price extraction, mm/dd parsing, return-time calculation
- [[Logger]] — `StreamToLogger`, `NoImportFilter`; stdout/stderr redirection
- [[Screenshot Store]] — save page + locator screenshots to the SQLite `binary_assets` table
- [[Storage State Store]] — load/save Playwright auth state; context options builder
- [[Migrate Mongo To SQLite]] — one-time CLI tool (legacy MongoDB → SQLite)

## See also

- [[_HOME]]
- [[01-Backend/_index|Backend]]
- [[Serializable Data Pattern]]
- [[Resource Path Resolution Pattern]]
