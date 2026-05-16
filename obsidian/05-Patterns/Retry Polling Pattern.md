---
tags: [pattern]
---

# Retry Polling Pattern

> Poll a condition with `time.time()` until it flips or the budget runs out; log every state transition.

## When to apply
Waiting for any dynamic UI element or state change on HoYoLab — a button enabling, an iframe loading, a reward animation finishing. Default budget: 180 seconds.

## The pattern
```python
deadline = time.time() + 180
last_state = None
while time.time() < deadline:
    state = read_state()
    if state != last_state:
        logger.info(f"State changed: {last_state} -> {state}")
        last_state = state
    if state == TARGET:
        return True
    time.sleep(0.5)
raise TimeoutError(f"Never reached {TARGET}, last seen {last_state}")
```

## Why
HoYoLab pages animate, stream, and re-render unpredictably. A flat `wait_for_selector` either fires too early (selector visible but interactive=false) or fails silently. Polling with transition logging makes the failure mode obvious in the log.

## Don't
- Don't poll faster than ~0.3s — you'll spam the page and trip rate limits.
- Don't omit transition logging — without it, "timeout after 180s" is unactionable.
- Don't use `page.wait_for_timeout()` as a substitute — fixed waits race with animations.

## See also
- [[_index]]
- [[RetryHelper]]
- [[EventNavigator]]
