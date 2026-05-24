---
tags: [frontend, components, common]
---

# SaveStatus

> Inline pill that reports the result of an auto-save: hidden when idle,
> spinner while saving, green check when saved, red retry chip on failure.

## How it works
Stateless presentational component driven by props from [[useAutoSave]]:
`status` (`"idle" | "saving" | "saved" | "error"`), `error`, and an optional
`onRetry` callback. Renders nothing when `status === "idle"` so a clean page
stays clean. The `"saved"` pill is held for 2s by `useAutoSave` before
collapsing back to idle. Failure state persists until the user clicks
**Retry** (which replays the last payload via `useAutoSave.retry`) or until
a subsequent save succeeds. Uses `themeColors.primary` for the saving
state and `COMMON_COLORS.success / error` for the discrete states, with
framer-motion fade/translate between transitions.

## Source
- `frontend/src/components/common/SaveStatus.jsx` — primary

## Depends on
- [[ThemeContext]] — theme accent
- [[Color Re-exports]] — success/error palette
- [[Framer Motion]] — pill transitions

## Used by
- [[ValueAdapter]] — pill mounted at the top of every dynamic form
- [[Shopping Page]] — pill in the header row next to Point/Duration
- [[Redeem Page]] — pill above the DataGrid

## See also
- [[_index]]
- [[useAutoSave]]
