---
tags: [backend, utils]
---

# Screenshot Store

> Stores Playwright page and locator screenshots as binary documents in MongoDB so the frontend can serve them via [[Asset Endpoints]].

## Source
- `backend/utils/screenshot_store.py` — primary

## How it works
All screenshots live in the `binary_assets` collection under id `screenshot:<filename>` and category `screenshot`. Filenames are sanitized to basename only (`Path(filename).name`) so an attacker-supplied subpath can't escape.

- `save_screenshot_bytes(filename, payload, metadata=None, content_type="image/png")` — `find_one_and_replace` upsert that records size, MIME, payload (`bson.Binary`), metadata dict, and `updated_at` (UTC). Returns the asset id.
- `save_page_screenshot(page, filename, full_page=False, metadata=None)` — calls `page.screenshot(full_page=...)` and saves. Adds `full_page` into metadata.
- `save_locator_screenshot(locator, filename, metadata=None)` — calls `locator.screenshot()` for element-only crops; used by [[LocatorTracker]] when a `Locator` object is available.
- `get_screenshot_bytes(filename)` — returns raw bytes or `None`.
- `get_screenshot_asset(filename)` — returns `{payload, content_type, metadata, source_path}` for the asset route.

## Depends on
- [[Mongo Connection]] — `get_db().binary_assets`
- [[Playwright]] — screenshot capture

## Used by
- [[LocatorTracker]] — all screenshot writes
- [[Asset Endpoints]] — `get_screenshot_asset`

## See also
- [[_index]]
- [[Locator Telemetry Pipeline]]
