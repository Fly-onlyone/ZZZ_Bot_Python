---
tags: [moc, patterns]
---

# Patterns — Map of Content

> Codebase conventions worth codifying. Knowing these prevents reinventing solutions
> the team has already settled on, and avoids stepping on the gotchas the patterns
> exist to dodge.

## Persistence & data

- [[Serializable Data Pattern]] — JSON dataclass mixin with `resource_path()`
- [[Resource Path Resolution Pattern]] — dev vs exe path handling
- [[Backup Collection Registration Pattern]] — register new Mongo collections in backup sets

## Handler & automation

- [[Handler Run Pattern]] — task class with standardized `run()` + result dict
- [[Image Comparison State Detection Pattern]] — OpenCV instead of fragile selectors
- [[Retry Polling Pattern]] — time-based polling with state-transition logging
- [[Three-Phase Hunt Execution Pattern]] — exchange-all → redeem-all → cleanup
- [[Centralized Selectors Pattern]] — all selectors in `Selectors.py`
- [[Locator Tracker Instrumentation Pattern]] — always pass `locator=` for element screenshots

## Frontend

- [[Dynamic Form ValueAdapter Pattern]] — auto-generate forms from JSON
- [[MUI Animation Component Prop Pattern]] — `component={motion.div}` not `motion(Paper)`
- [[SSE Event Bus Pattern]] — backend EventBus → frontend useTaskEvents

## See also

- [[_HOME]]
