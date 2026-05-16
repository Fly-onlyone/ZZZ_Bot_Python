---
tags: [architecture, flow]
---

# Notification Pipeline

> Two parallel notification channels: HTML email (Jinja2 + Apprise SMTP) for daily
> mission reports, and live frontend SSE for in-app task progress. Both fan out from
> the same handlers that produce result dicts during [[Daily Task Cycle]].

## Source

- `backend/core/Notification.py` — Jinja2 + Apprise sender
- `backend/core/event_bus.py` — thread-safe SSE broadcaster
- `backend/message/` — HTML templates
- `frontend/src/hooks/useTaskEvents.js` — SSE consumer

## How it works

```mermaid
flowchart LR
    H[Handlers produce result dicts] --> EB[Event Bus emit]
    EB --> SSE[/events SSE endpoint]
    SSE --> FE[useTaskEvents]
    FE --> UI[Status updates in UI]

    H --> NS[Notification Sender]
    NS --> J[Jinja2 render with base64 screenshots]
    J --> AP[Apprise]
    AP --> SMTP[(Gmail SMTP)]
    NS --> D[Desktop toast via NotificationHelper]
```

The Event Bus uses stdlib `Queue` and is safe to call from any thread (handlers run
on worker threads, FastAPI on its own loop). Mission email scheduling is async unless
`exit_after_run` is set — then it blocks so the email lands before sidecar shutdown.

## Depends on

- [[Notification Sender]] — email
- [[Mission Email Scheduler]] — sync vs async dispatch
- [[Event Bus]] — SSE broadcaster
- [[NotificationHelper]] — Windows desktop toasts
- [[Mission Email Template]] — Jinja2 source
- [[Apprise]], [[Jinja2]] — integration libs
- [[SSE Event Bus Pattern]] — the pattern this implements

## Used by

- [[Daily Task Cycle]] — sends one email per run
- [[useTaskEvents]] — frontend consumer

## Gotchas

- Embedding screenshots as base64 inflates email size — large mission reports may hit Gmail's 25MB limit.
- SSE connections drop on Windows sleep/wake; `useTaskEvents` reconnects but may miss events emitted during the gap.

## See also

- [[_index]]
- [[SSE Event Bus Pattern]]
- [[Event Bus]]
- [[Notification Sender]]
