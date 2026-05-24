---
tags: [backend, utils]
---

# Screenshot Store

> Stores Playwright page and locator screenshots as binary rows in the SQLite `binary_assets` table so the frontend can serve them via [[Asset Endpoints]].

## Source
- `backend/utils/screenshot_store.py` — primary

## How it works
All screenshots live in the `binary_assets` table under id `screenshot:<filename>` and category `screenshot`. Filenames are sanitized to basename only (`Path(filename).name`) so an attacker-supplied subpath can't escape. The store does not touch the database directly — it delegates to [[DataStore]]'s binary-asset functions.

- `save_screenshot_bytes(filename, payload, metadata=None, content_type="image/png")` — calls `DataStore.upsert_binary_asset`, recording size, MIME, the payload as a `BLOB`, metadata dict, `updated_at`, and an `expires_at` for retention. Returns the asset id.
- `save_page_screenshot(page, filename, full_page=False, metadata=None)` — calls `page.screenshot(full_page=...)` and saves. Adds `full_page` into metadata.
- `save_locator_screenshot(locator, filename, metadata=None)` — calls `locator.screenshot()` for element-only crops; used by [[LocatorTracker]] when a `Locator` object is available.
- `get_screenshot_bytes(filename)` — returns raw bytes or `None` via `DataStore.get_binary_asset`.
- `get_screenshot_asset(filename)` — returns `{payload, content_type, metadata, source_path}` for the asset route.

## Depends on
- [[DataStore]] — `upsert_binary_asset`, `get_binary_asset`
- [[Playwright]] — screenshot capture

## Used by
- [[LocatorTracker]] — all screenshot writes
- [[Asset Endpoints]] — `get_screenshot_asset`

## See also
- [[_index]]
- [[Locator Telemetry Pipeline]]
