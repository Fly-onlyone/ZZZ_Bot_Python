---
tags: [backend, core]
---

# Event Bus

> Thread-safe stdlib `queue.Queue` broadcaster used by SSE endpoints to fan out events to every connected frontend client.

## Source

- `backend/core/event_bus.py` — primary implementation

## How it works

`subscribe(maxsize=100)` registers a new bounded `Queue` and returns it to the SSE handler. `unsubscribe(q)` removes it. `emit(event_type, data)` serializes `data` as JSON once, then iterates a snapshot of subscriber queues under a lock and pushes `(event_type, payload)` tuples via `put_nowait`.

When a subscriber queue is full, the event is **dropped for that subscriber** (logged at warning level) rather than blocking the producer. This keeps automation threads — playwright task, hunt mode, scheduler — from stalling on slow SSE consumers.

Events are dispatched from threading contexts only (no asyncio), so the stdlib queue suffices.

## Depends on

- *(no runtime dependencies — stdlib only)*

## Used by

- [[Bot Entry Point]] — emits `task-completed` after `playwright_task()`
- [[HuntModeHandler]] — emits `task-completed` after hunt run
- [[System Endpoints]] — SSE route that subscribes/unsubscribes client queues

## Gotchas

- Events for full queues are silently dropped (per-subscriber); good for fan-out, bad if you need delivery guarantees.
- Iteration uses a list snapshot so subscribe/unsubscribe during `emit` is safe.

## See also

- [[_index]]
- [[SSE Event Bus Pattern]]
