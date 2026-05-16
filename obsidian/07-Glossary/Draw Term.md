---
tags: [glossary]
---

# Draw

> A prize lottery on a HoYoLab event page — spin a wheel or open a chest for a random reward.

## How it works
Draws are handled by [[DrawHandler]]. The page typically spins an animation and reveals a reward image; the handler identifies the reward via [[Image Comparison State Detection Pattern]] against the `reward image/` reference set, then records the result for the [[Notification Pipeline]]. Some draws yield codes that flow into [[RedeemAutofill]] automatically.

## See also
- [[_index]]
- [[DrawHandler]]
- [[Image Recognition Pipeline]]
