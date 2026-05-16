---
tags: [backend, automation]
---

# Selectors

> Single source of truth for every CSS selector and UI text constant used against the HoYoLab event page.

## Source
- `backend/automation/Selectors.py` — primary

## How it works
The module is a flat list of module-level constants grouped by feature with banner comments:

- **Mission** — dialog close/body, wrapper, avatars, task item rows.
- **Shopping** — screen, item card, name/price/button, current points bubble, redeem code copy controls.
- **Draw** — screen, action wrap button, confirm dialog, reward image, limit text and number.
- **Common** — shared avatar + dialog-close selectors reused across panels.
- **Text constants** — `EXCHANGE_BUTTON_TEXT`, `CLAIMED_POPUP_TEXT`, `MISSION_BUTTON_TEXT` for `get_by_text` lookups.

Many class names are hashed (`-O3T67n`, `-hsQFy-`) because HoYoLab ships compiled CSS; when the site updates, this is usually the only file that needs to change.

## Depends on
- *(none — leaf module)*

## Used by
- [[MissionHandler]], [[ShoppingHandler]], [[DrawHandler]], [[HuntModeHandler]]
- [[EventNavigator]] — panel close + back-button helpers
- [[RedeemAutofill]] — share text constants

## Gotchas
- Hashed selectors break on every HoYoLab refresh — verify against the live site before debugging handler bugs.

## See also
- [[_index]]
- [[Centralized Selectors Pattern]]
- [[HoYoLab]]
