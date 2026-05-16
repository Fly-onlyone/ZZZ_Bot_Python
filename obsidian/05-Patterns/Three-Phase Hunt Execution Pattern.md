---
tags: [pattern]
---

# Three-Phase Hunt Execution Pattern

> Exchange-all-then-redeem: collect every redemption code before any side effect, then bulk-redeem, then clean up only what actually succeeded.

## When to apply
Hunt mode — buying timed-window items that yield codes which must each be redeemed elsewhere. Applies whenever multiple actions must all complete before any commit.

## The pattern
```python
# Phase 1: exchange every hunt item, collect codes
codes = []
for item in hunt_items:
    code = exchange(item)
    if code:
        codes.append((item, code))

# Phase 2: bulk-redeem all collected codes
results = [(item, redeem(code)) for item, code in codes]

# Phase 3: remove only successfully-redeemed items from hunt list
for item, ok in results:
    if ok:
        hunt_list.remove(item)
hunt_list.save()
```

## Why
A partial failure mid-exchange used to leave codes uncollected — the user lost both the shop spend and the reward. Decoupling exchange from redemption ensures every code is captured before any redemption can fail. Cleanup only removes items that actually completed end-to-end.

## Don't
- Don't interleave exchange and redeem in a single loop — a redeem failure cancels later exchanges.
- Don't remove from the hunt list before redeem confirms — you'll silently lose retry ability.
- Don't swallow exchange exceptions; log and keep the partial codes list intact.

## See also
- [[_index]]
- [[HuntModeHandler]]
- [[Hunt Mode Lifecycle]]
