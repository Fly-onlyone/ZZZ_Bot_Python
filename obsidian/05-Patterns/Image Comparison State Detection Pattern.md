---
tags: [pattern]
---

# Image Comparison State Detection Pattern

> Detect UI states by `cv2.matchTemplate`-ing a screenshot crop against a reference PNG, not by CSS selector.

## When to apply
Any state read on the HoYoLab event site — button labels (Finished / Unfinished / Reward), avatar identification, reward recognition from the prize draw wheel.

## The pattern
```python
# Compare crop against "sample/button_exchange.png"
# Threshold: <5% difference indicates Exchange state
reference = cv2.imread(resource_path("sample/button_exchange.png"))
crop = capture_element(locator)
diff = compare_images(crop, reference)
logger.info(f"Exchange match: diff={diff:.3f}")
if diff < 0.05:
    return ButtonState.EXCHANGE
```

## Why
HoYoLab selectors break frequently — class names hash on every deploy, copy changes between events, the same button has three different DOMs across pages. A pixel-level template is stable as long as the art is stable.

## Don't
- Don't use relative paths with OpenCV — always `resource_path()` so the exe finds the bundled PNG.
- Don't skip logging the diff value — when matches drift, that log line is the only forensic.
- Don't add fallback CSS selectors silently; either the image matches or it doesn't.

## See also
- [[_index]]
- [[ImageProcessor]]
- [[Image Recognition Pipeline]]
- [[Image Comparison Strategy]]
