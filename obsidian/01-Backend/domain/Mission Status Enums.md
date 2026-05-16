---
tags: [backend, domain]
---

# Mission Status Enums

> String enums shared between backend state machines and the frontend UI — derived from the constants used in image recognition and HoYoLab response strings.

## Source

- `backend/domain/models.py` — primary implementation

## How it works

All enums inherit from `(str, Enum)` so their `.value` is JSON-serializable and direct equality with raw strings works.

- **`MissionStatus`** — `FINISHED="Finished"`, `UNFINISHED="Unfinished"`, `REWARD="Reward"`. Returned by image-comparison detection of the mission button state.
- **`CheckInStatus`** — `SUCCESS="Login Success"`, `FAILED="Login Failed"`, `LINK_NOT_OPENED="Link isn't opened"`. Persisted on `DailyMissionReport.check_in` and surfaced in the mission email.
- **`ButtonState`** — `FINISHED`, `UNFINISHED`, `REWARD`, `UNKNOWN="unknown"`. Same values as `MissionStatus` plus an unknown sentinel that [[ImageProcessor]] returns when no reference image matched.
- **`ItemAvailability`** — `EXCHANGE="Exchange"`, `LIMIT_REACHED="Limit Reached"`, `COUNTDOWN="countdown"`. The actual countdown timer text is stored verbatim; `COUNTDOWN` is the abstract category.

## Depends on

- *(no runtime dependencies — pure enums)*

## Used by

- [[Domain Models]] — comparisons inside `is_finished`, `is_available_for_exchange`, etc.
- [[MissionHandler]] — string equality on `"Finished"` etc.
- [[ImageProcessor]] — returns these string values from `detect_button_state`

## Gotchas

- Two enums (`MissionStatus` and `ButtonState`) overlap by design — `ButtonState` exists to add the `UNKNOWN` sentinel without polluting persisted reports.

## See also

- [[_index]]
- [[Domain Models]]
- [[Image Comparison State Detection Pattern]]
