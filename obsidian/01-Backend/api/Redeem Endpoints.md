---
tags: [backend, api]
---

# Redeem Endpoints

> Read and bulk-replace the redemption-code history used by the redeem page.

## Source
- `backend/api/routes.py` — primary

## How it works
- `GET /redeem` returns `MongoRepository.get_redemptions()` — a list of records persisted by the redeem flow.
- `POST /redeem` accepts a list of `RedeemItem` Pydantic models, serializes each via `model_dump()`, then calls `MongoRepository.replace_all_redemptions(...)`. This is a full replace, not an append; the frontend is expected to send the whole desired list.

Redemption records are written incrementally during runs by [[ShoppingHandler]] and [[DrawHandler]] through `save_redeem_data()` in [[DataHandler]]; this endpoint covers the management UI path only.

## Depends on
- [[MongoRepository]] — `get_redemptions`, `replace_all_redemptions`
- [[Domain Models]] — `RedeemItem`

## Used by
- [[Redeem Page]] — edit / clear history

## See also
- [[_index]]
- [[DataHandler]]
