---
tags: [integration]
---

# Apprise

> Multi-channel notification library; in this project used for SMTP email delivery (Gmail), with the door open to add Telegram, Discord, etc. without code changes.

## Used for
- [[Notification Pipeline]] — sends rendered HTML emails after each task cycle
- Error alerts when a handler fails

## Configuration
- Version `apprise==1.9.5` (`pyproject.toml`)
- Gmail credentials stored in `output/account.json` (see [[Account Endpoints]])
- `apprise.plugins.email.*` submodules are explicitly collected by `BotSidecar.spec` (PyInstaller can't auto-detect them)

## Wire-up
- `backend/core/Notification Sender.py` — builds the `Apprise()` instance + `notify()` call
- `backend/utils/NotificationHelper.py` — assembles the email body via Jinja2 then hands off to Apprise

## Auth mode
SMTP credentials (Gmail app password); the URL format `mailto://user:apppass@gmail.com` encodes the auth.

## Gotchas
- PyInstaller spec must `collect_submodules("apprise.plugins.email")` and `collect_data_files(..., include_py_files=True, includes=["plugins/email/**/*"])` — otherwise email delivery silently fails in the packaged exe.

## See also
- [[_index]]
- [[Jinja2]]
- [[Notification Sender]]
