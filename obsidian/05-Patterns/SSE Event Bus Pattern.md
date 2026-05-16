---
tags: [pattern]
---

# SSE Event Bus Pattern

> Backend handlers publish to the in-process Event Bus, an SSE endpoint streams those events, and the React hook `useTaskEvents` consumes them.

## When to apply
Any task-progress update the UI needs to react to live — mission-step transitions, hunt-phase changes, shopping progress, error notifications.

## The pattern
```
Handler.run()
  └─ event_bus.publish({"type": "mission.step", "step": "checkin", "status": "ok"})
       └─ SSE endpoint (/events) streams JSON lines
            └─ useTaskEvents() in React subscribes via EventSource
                 └─ updates TanStack Query cache → components re-render
```

Handlers stay synchronous and decoupled — they just publish; the bus fans out.

## Why
Polling the backend for task state would either lag (slow polling) or hammer it (fast polling). SSE pushes only when something changes, and one persistent connection per browser keeps it cheap. Decoupling via the bus lets new subscribers be added without touching handlers.

## Don't
- Don't `await` consumers in `publish()` — the bus must stay non-blocking so handlers don't stall.
- Don't push high-frequency events (>10/s) — coalesce upstream or you'll choke the SSE pipe.
- Don't use SSE for two-way communication; that's what the REST endpoints are for.

## See also
- [[_index]]
- [[Event Bus]]
- [[useTaskEvents]]
- [[Frontend Data Flow]]
