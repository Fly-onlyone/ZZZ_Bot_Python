---
tags: [backend, utils]
---

# StringUtil

> Small regex / datetime helpers shared by handlers for parsing item availability, prices, and event durations.

## Source
- `backend/utils/StringUtil.py` — primary

## How it works
- `extract_number_from_string(s)` — first digit run in a string as `int` (`None` if no match).
- `extract_price(s)` — alias-style helper used by shopping for cost strings.
- `extract_number(s, side="left"|"right")` — parses `"N/M"` inventory strings (e.g. `"3/5"`).
- `extract_and_convert_duration(s)` — pulls `Duration: dd/mm – dd/mm` strings and returns `{Start: "mm/dd", End: "mm/dd"}` for event date math.
- `calculate_return_time(input)` — input is `"H:M:S"`; adds that delta to `datetime.now()` and returns `"HH:MM dd/mm/yy"`. Used by [[Shopping Endpoints]] `/overview/hunt` and [[HuntModeHandler]] to convert countdown strings into absolute hunt times.
- `clean_leading_dots(path)` — strips repeated leading `./` or `../` from a path string.

All functions are pure and stateless; safe to call from any thread.

## Depends on
- *(stdlib only: `re`, `datetime`)*

## Used by
- [[HuntModeHandler]] — countdown → absolute time
- [[Shopping Endpoints]] — `/overview/hunt` computation
- [[ShoppingHandler]] — price / inventory parsing

## See also
- [[_index]]
- [[Hunt Mode Lifecycle]]
