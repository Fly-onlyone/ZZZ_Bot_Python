---
tags: [integration]
---

# OpenCV

> Computer vision library used for template matching (button state detection, reward identification) and ORB feature matching (avatar fingerprinting) — replaces brittle DOM selectors.

## Used for
- [[Image Recognition Pipeline]] — `cv2.matchTemplate` for button states
- [[Image Comparison Strategy]] — pluggable comparison strategies
- Game avatar detection (ZZZ vs other HoYoverse games on the event page)
- Reward recognition from prize draw screenshots

## Configuration
- Version `opencv-python==4.12.0.88` (`pyproject.toml`)
- Reference templates in `sample/` (button states) and `reward image/` (draw rewards) — bundled into the sidecar by `BotSidecar.spec`
- Match threshold: <5% pixel difference (see code-guide Pattern 3)

## Wire-up
- `backend/automation/ImageProcessor.py` — main comparison entry point
- `backend/strategies/` — Strategy pattern for swapping comparison algorithms
- `backend/handlers/MissionHandler.py` — calls comparator for Finished/Unfinished/Reward states

## Auth mode
N/A

## Gotchas
- All image paths must go through `resource_path()` — OpenCV chokes on relative paths in PyInstaller mode.
- NumPy 2.x compatibility is fragile; `BotSidecar.spec` hand-collects `numpy.libs` delvewheel DLLs (OpenBLAS / MSVCP).

## See also
- [[_index]]
- [[Image Recognition Pipeline]]
- [[ImageProcessor]]
