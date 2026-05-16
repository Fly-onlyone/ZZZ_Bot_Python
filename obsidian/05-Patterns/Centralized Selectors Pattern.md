---
tags: [pattern]
---

# Centralized Selectors Pattern

> Every CSS / XPath selector lives in `backend/automation/Selectors.py` — handlers import, never hardcode.

## When to apply
Any web automation reaching into the HoYoLab DOM. Even one-off selectors go in `Selectors.py`.

## The pattern
```python
# backend/automation/Selectors.py
class Selectors:
    LOGIN_BUTTON = "button[data-cy='login']"
    REWARD_PANEL = "div.reward-panel"

# handler
from backend.automation.Selectors import Selectors
page.click(Selectors.LOGIN_BUTTON)
```

## Why
HoYoLab redesigns event pages every few weeks. When a class hash flips, a single file gets edited — not seven handlers. Also makes selector audits trivial: open `Selectors.py`, see every coupling to the upstream DOM.

## Don't
- Don't sprinkle string literals across handlers — they will rot in place.
- Don't duplicate the same selector under two names in `Selectors.py`; one name per element.
- Don't put selectors in [[ImageProcessor]] — image matching is the alternative to selectors, not the home for them.

## See also
- [[_index]]
- [[Selectors]]
- [[EventNavigator]]
- [[Image Comparison State Detection Pattern]]
