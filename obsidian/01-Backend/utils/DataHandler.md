---
tags: [backend, utils]
---

# DataHandler

> Provides the `Serializable` JSON mixin plus thin MongoDB-bridging helpers for mission, shopping, and redeem records.

## Source
- `backend/utils/DataHandler.py` — primary

## How it works
- `Serializable` — base class with `save(file_path)` (writes `asdict(self)` as indented JSON) and `load(file_path)` (creates a default-constructed instance + file when missing). Backs [[Settings Contract]] and [[GlobalVar]] dataclasses.
- `prepare_mission_data(...)` — pulls all mission docs from MongoDB, locates today's record by `dd/mm/YYYY`, and appends a placeholder when missing. Returns `(previous_data, todays_data)` so handlers can mutate `todays_data` in place.
- `maintain_mission_data(...)` — upserts today's record via `mongo.save_mission_day(...)`. TTL index handles 5-day rotation.
- `load_shopping_data` / `save_shopping_data` — shopping doc round-trip with merge-on-save.
- `save_redeem_data(...)` — appends or updates a redemption entry (creates new doc if `record_id is None`, otherwise updates). TTL index handles 30-day cleanup.

`file_path` arguments on the shopping/redeem helpers are vestigial — kept for call-site compatibility after the MongoDB migration.

## Depends on
- [[MongoRepository]] — all data ops

## Used by
- [[MissionHandler]] — mission record flow
- [[ShoppingHandler]] — redeem entries
- [[DrawHandler]] — redeem entries
- [[Mission Endpoints]] — record shape

## See also
- [[_index]]
- [[Serializable Data Pattern]]
