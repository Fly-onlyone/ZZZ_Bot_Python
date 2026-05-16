---
tags: [backend, api]
---

# Asset Endpoints

> Serves binary screenshot assets stored in MongoDB to the frontend.

## Source
- `backend/api/routes.py` — primary

## How it works
`GET /assets/screenshot/{filename}` sanitizes the filename with `Path(filename).name` (strips directory traversal), then calls `get_screenshot_asset()` from [[Screenshot Store]]. The asset document carries the original `payload` (binary), `content_type`, and metadata. The response sets `Cache-Control: no-store` so the frontend always re-fetches the freshest capture — important when a selector is re-hit and the screenshot rotates.

Missing or invalid filenames return `400` / `404` JSON errors instead of binary bodies.

## Depends on
- [[Screenshot Store]] — `get_screenshot_asset`

## Used by
- [[Locator Tracker Page]] — page + element screenshot thumbnails
- [[Mission Email Template]] — does NOT use this; templates embed images differently

## Gotchas
- `no-store` means heavy traffic re-downloads bytes on every render; the locator page paginates to keep this bounded.

## See also
- [[_index]]
- [[Locator Telemetry Pipeline]]
