---
tags: [glossary]
---

# TTL

> A MongoDB time-to-live index that auto-deletes documents whose timestamp field is older than a configured threshold.

## How it works
TTL indexes are created with `db.coll.create_index("ts", expireAfterSeconds=N)`. Mongo's background `TTLMonitor` thread (default 60s tick) deletes expired docs without application code. ZZZ Bot uses a 7-day TTL on the `locator_tracker` collection so locator telemetry self-cleans — see [[LocatorTracker]]. TTL deletion is best-effort, not real-time, so a doc may linger a minute past its expiry.

## See also
- [[_index]]
- [[MongoDB]]
- [[LocatorTracker]]
