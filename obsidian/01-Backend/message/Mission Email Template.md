---
tags: [backend, message]
---

# Mission Email Template

> Jinja2 HTML template for the daily mission-report email sent after every run.

## Source
- `backend/message/mission.html.jinja` — primary

## How it works
Single self-contained HTML email rendered by [[Notification Sender]] / [[Notification Pipeline]] using Jinja2. Expected template variables:

- `theme` — one of `nebula`, `venom`, `glacier`, `cyber` (plus legacy `green`, `purple`, `blue` aliases). The template defines an inline `theme_colors` dict and falls back to `nebula` for unknown values, so primary, secondary, light, and alpha CSS colors all flow from this single string.
- `day` — date string for the header (`dd/mm/YYYY`).
- `check_in` — text status; the literal `"Login Success"` triggers the green success badge AND renders the `login_reward_image` block.
- `login_reward_image` — CID or data URI for the inline reward screenshot (only used when check-in succeeded).
- `missions` — list of `{name, state}` dicts. `state == "Finished"` styles the row + chip green; anything else renders red. The stats grid counts total and `selectattr('state', 'equalto', 'Finished')` for the completed badge.

Layout: container card, themed header, check-in badge, optional reward image, stats grid (Total / Completed), and a per-mission status table. Email-safe styles (inline + scoped `<style>`, no external CSS).

## Depends on
- [[Jinja2]] — render engine
- [[Notification Sender]] — sender + image embedding
- [[DataHandler]] — supplies `missions` and `check_in` shape

## Used by
- [[Notification Pipeline]] — daily report email
- [[Mission Endpoints]] — same data shape served to the UI

## See also
- [[_index]]
- [[Daily Task Cycle]]
