---
tags: [backend, domain]
---

# Domain Models

> Dataclass schemas for the business entities the bot manipulates: mission records, daily reports, shopping items and bundles, redemption codes, and hunt targets.

## Source

- `backend/domain/models.py` — primary implementation

## How it works

All models are stdlib `@dataclass` with helper methods. Grouped into three families:

**Mission family**
- `MissionRecord(name, state)` with `is_finished()`.
- `DailyMissionReport(day, check_in, missions)` with `create_for_today()`, `add_mission()`, `get_mission()`.

**Shopping family**
- `ShoppingItem(name, price, inventory, available)` with `is_available_for_exchange()`, `is_on_cooldown()` (detects `/` and `:` in `available`), `is_limit_reached()`.
- `EventDuration(start, end)` with `is_active()` — parses `dd/mm` and assumes the current year.
- `ShoppingData(point, duration, items, selected, purchased, hunt)` with `get_selected_items()`, `get_hunt_items()`, `mark_as_purchased()`.

**Redemption / hunt family**
- `RedemptionCode(item_name, code, day, state)` with `create_now()` (timestamps as `HH:MM dd/mm/YYYY`) and `is_older_than_days(days)` for retention.
- `HuntTarget(name, scheduled_time, price, inventory)` and `HuntInfo(enabled, hunt_items, next_hunt_time)`.

## Depends on

- [[Mission Status Enums]] — the state strings these models compare against

## Used by

- [[MissionHandler]], [[ShoppingHandler]], [[HuntModeHandler]] — operate on dict shapes that mirror these models
- [[DataStore]] — persists matching JSON
- [[Frontend Data Flow]] — REST payloads mirror these field names

## Gotchas

- Handlers still pass raw `dict` payloads in many places; these dataclasses document the shape rather than enforce it everywhere.
- `EventDuration` assumes the start/end fall in the **current** year — events spanning Dec/Jan need extra handling.

## See also

- [[_index]]
- [[Mission Status Enums]]
- [[Serializable Data Pattern]]
