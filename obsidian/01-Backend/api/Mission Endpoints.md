---
tags: [backend, api]
---

# Mission Endpoints

> Today's mission completion report for the overview dashboard.

## Source
- `backend/api/routes.py` — primary

## How it works
`GET /overview/mission` formats today's date as `dd/mm/YYYY` and asks [[MongoRepository]] `get_today_mission()` for the matching record. When no record exists yet (no run has happened today), it returns a placeholder:

```python
{"day": today_str, "check_in": "Link isn't opened", "missions": []}
```

Returned shape matches the document written by [[MissionHandler]] through `prepare_mission_data()` / `maintain_mission_data()` in [[DataHandler]]: each mission has `name` and `state` fields, plus a top-level `check_in` string that the [[Mission Email Template]] also consumes.

## Depends on
- [[MongoRepository]] — `get_today_mission`
- [[DataHandler]] — shape contract

## Used by
- [[Mission Section]] — Overview page table

## See also
- [[_index]]
- [[Daily Task Cycle]]
