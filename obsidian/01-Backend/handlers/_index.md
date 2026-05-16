---
tags: [moc, backend, handlers]
---

# Backend / handlers — Map of Content

> Per-feature task orchestrators. Each handler exposes a `run()` method that the
> top-level scheduler calls inside a shared Playwright session.

## Handlers

- [[MissionHandler]] — daily check-in + mission completion + reward collection
- [[ShoppingHandler]] — item exchange + redemption code harvesting
- [[DrawHandler]] — prize lottery + reward detection via image comparison
- [[HuntModeHandler]] — background timed shop polling; calls ShoppingHandler on hit

## See also

- [[_HOME]]
- [[01-Backend/_index|Backend]]
- [[Daily Task Cycle]]
- [[Hunt Mode Lifecycle]]
- [[Handler Run Pattern]]
- [[Three-Phase Hunt Execution Pattern]]
