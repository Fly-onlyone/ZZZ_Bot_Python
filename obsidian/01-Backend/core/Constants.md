---
tags: [backend, core]
---

# Constants

> Centralized magic numbers for image thresholds, HTTP pool sizes, timeouts, retention windows, retry counts, URLs, and selectors.

## Source

- `backend/core/constants.py` — primary implementation

## How it works

Organized into labeled sections:

- **Image comparison:** `IMAGE_MATCH_THRESHOLD = 5.0` (max % difference for a match), `IMAGE_BINARY_THRESHOLD = 30`.
- **HTTP pool:** `HTTP_POOL_CONNECTIONS = 10`, `HTTP_POOL_MAX_SIZE = 20`, `HTTP_MAX_RETRIES = 3`.
- **Timeouts (ms):** dialog 5000, mission click 2000, retry 1000, network idle 10000.
- **Retention:** missions 5 days, redemption codes 30 days.
- **Hunt buffer:** `HUNT_WAIT_BUFFER_SECONDS = 120` — schedule fires 2 min before item time.
- **Selectors:** all dialog, mission, and shopping CSS selectors plus `PANEL_BACK_SELECTOR`.
- **Logging:** daily rotation, 7 backups.

Imported throughout handlers, automation, and strategies to keep tunables in one place.

## Depends on

- *(no runtime dependencies — pure constants)*

## Used by

- [[Image Comparison Strategy]] — `IMAGE_MATCH_THRESHOLD`, `IMAGE_BINARY_THRESHOLD`
- [[MissionHandler]], [[ShoppingHandler]], [[HuntModeHandler]] — selectors, timeouts
- [[Bot Entry Point]] — `HUNT_WAIT_BUFFER_SECONDS` via the handler re-export

## Gotchas

- Selector strings are duplicated in [[Selectors]] for shopping/draw; mission selectors still live here directly.

## See also

- [[_index]]
- [[Centralized Selectors Pattern]]
