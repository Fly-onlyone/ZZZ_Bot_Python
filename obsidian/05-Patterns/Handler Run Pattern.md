---
tags: [pattern]
---

# Handler Run Pattern

> A handler is a single class with one `run()` entry point that returns a result dict the notifier can render.

## When to apply
Any task-specific automation workflow scheduled by `Bot.py` — missions, shopping, draws, hunt.

## The pattern
```python
class MissionHandler:
    def __init__(self, page):
        self.page = page

    def run(self) -> dict:
        try:
            # ... automation steps ...
            return {"status": "ok", "completed": [...], "errors": []}
        except Exception as e:
            logger.exception("Mission failed")
            return {"status": "error", "message": str(e)}
```

## Why
A uniform interface lets the scheduler treat every handler the same way: call `run()`, feed the result into the notification pipeline, log, move on. Graceful degradation — a failing handler shouldn't block the rest of the cycle.

## Don't
- Don't raise out of `run()` — catch, log, and return an error dict so the cycle continues.
- Don't push UI state from inside the handler — emit via the [[Event Bus]] instead.
- Don't write docstrings restating the run sequence — that's documented in [[Daily Task Cycle]].

## See also
- [[_index]]
- [[MissionHandler]]
- [[ShoppingHandler]]
- [[HuntModeHandler]]
- [[DrawHandler]]
