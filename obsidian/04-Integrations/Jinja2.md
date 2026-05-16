---
tags: [integration]
---

# Jinja2

> Template engine used to render HTML email bodies for mission summaries, hunt reports, and error notifications.

## Used for
- [[Notification Pipeline]] — HTML email bodies
- [[Mission Email Template]] — daily mission report layout

## Configuration
- Version `jinja2==3.1.6` (`pyproject.toml`)
- Templates live in `backend/message/` (bundled into the sidecar by `BotSidecar.spec`)

## Wire-up
- `backend/core/Notification Sender.py` — loads + renders templates with `Environment(loader=FileSystemLoader(...))`
- `backend/utils/NotificationHelper.py` — builds the context dicts
- `backend/message/*.html` — actual templates

## Auth mode
N/A

## Gotchas
- Template paths must go through `resource_path()` — bundled templates live under `backend/message/` in the PyInstaller `_MEI` directory, not the source tree.

## See also
- [[_index]]
- [[Apprise]]
- [[Notification Sender]]
