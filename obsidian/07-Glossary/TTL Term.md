---
tags: [glossary]
---

# TTL

> Time-to-live — a retention window after which a stored record is considered stale and deleted.

## How it works
MongoDB once provided TTL natively via TTL indexes and a background `TTLMonitor` thread. **SQLite has no equivalent**, so ZZZ Bot implements retention in application code:

- Rows in TTL tables (`missions`, `redemptions`, `locator_tracker`, `locator_tracker_failures`, `binary_assets`) carry an `expires_at` column set at insert time.
- `DataStore.purge_expired()` runs `DELETE … WHERE expires_at < now`. It is called once at startup inside `ensure_schema()` and, throttled to once per 60s, before reads of TTL tables.

Retention windows: missions 5 days, redemptions 30 days, locator telemetry 7 days. Because purge is event-driven, an expired row can linger until the next startup or TTL-table read.

Critical gotcha: any **new** TTL table must add its name to `purge_expired()` and include an `expires_at` column — otherwise its rows never expire.

## See also
- [[_index]]
- [[SQLite]]
- [[DataStore]]
- [[LocatorTracker]]
