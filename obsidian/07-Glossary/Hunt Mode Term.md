---
tags: [glossary]
---

# Hunt Mode

> A timed-window strategy that polls the HoYoLab shop and snipes specific items the moment they re-stock.

## How it works
Hunt mode is opt-in via `enable_hunt_mode` in `settings.json`, and it only runs while the `run_task` master automation switch is also enabled. Items the user wants to hunt are flagged in the `Hunt` array of `shopping.json` — a subset of `Selected`. [[HuntModeHandler]] polls on its own schedule and, when stock returns, runs the [[Three-Phase Hunt Execution Pattern]]: exchange all hunt items, bulk-redeem the resulting codes, then prune the hunt list of items that fully succeeded.

## See also
- [[_index]]
- [[Hunt Mode Lifecycle]]
- [[Three-Phase Hunt Execution Pattern]]
