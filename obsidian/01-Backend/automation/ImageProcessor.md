---
tags: [backend, automation]
---

# ImageProcessor

> OpenCV-backed image comparison and visual state detection for HoYoLab UI elements.

## Source
- `backend/automation/ImageProcessor.py` — primary

## How it works
Three public entry points back the [[Image Recognition Pipeline]]:

1. `compare_images()` — absolute diff + binary threshold, returns a 0–100 % mismatch score; `<5%` (`IMAGE_MATCH_THRESHOLD`) counts as a match.
2. `find_correct_avatar()` — iterates avatar locators and matches each one against the bundled ZZZ icon to pick the right game tile.
3. `detect_reward()` — sweeps `reward image/` references against a draw locator to label the prize; falls back to `"Unknown reward"`.

`ImageProcessor.detect_button_state()` classifies mission buttons as `Finished` / `Unfinished` / `Reward`. A shared `requests.Session` with a pooled adapter (configurable retries) fetches remote images, and `fetch_image_from_locator()` resolves `<img>`, background-image, data-URI, and screenshot fallbacks.

## Depends on
- [[OpenCV]] — template matching primitives
- [[Constants]] — thresholds and HTTP pool sizes
- [[RetryHelper]] — `retry_until_non_zero_count` while waiting for avatars
- [[Tracking Helpers]] — `safe_track` on lottery logo match

## Used by
- [[MissionHandler]] — button state detection
- [[DrawHandler]] — lottery logo + reward identification
- [[ShoppingHandler]] — avatar gating

## Gotchas
- Reference PNGs must resolve via [[Resource Path Resolution Pattern]]; missing files raise during compare.
- HTTP session is process-wide — never close it manually.

## See also
- [[_index]]
- [[Image Comparison State Detection Pattern]]
- [[Image Recognition Pipeline]]
