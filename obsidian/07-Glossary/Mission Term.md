---
tags: [glossary]
---

# Mission

> A daily check-in or repeatable task on HoYoLab — claim a reward by visiting the page, watching a short video, or pressing a button.

## How it works
Missions are what [[MissionHandler]] runs every cycle. Each mission has a state — `Unfinished`, `Finished`, or `Reward` (claimable) — detected via the [[Image Comparison State Detection Pattern]]. The handler walks the daily list, claims everything claimable, records the outcome in the missions collection, and emits a result dict the [[Notification Pipeline]] formats into an email.

## See also
- [[_index]]
- [[Mission Status Enums]]
- [[Daily Task Cycle]]
