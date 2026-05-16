---
tags: [operations]
---

# Logging Setup

> `TimedRotatingFileHandler` with 7-day retention writes to `backend/logs/`; a `NoImportFilter` strips noisy import lines; in exe mode stdout/stderr are also redirected into the log file.

## Source
- `backend/utils/Logger.py`
- `backend/logs/` — runtime output

## How it works
On startup [[Logger]] configures a root logger with `TimedRotatingFileHandler(when="midnight", backupCount=7)` so logs rotate nightly and only the last seven days are kept. A custom `NoImportFilter` drops `import` chatter from third-party libraries to keep the file focused on automation events.

In exe mode (`sys.frozen`) there is no console attached, so stdout and stderr are redirected into the same log file — otherwise unhandled prints would disappear. Log paths flow through [[Resource Path Resolution Pattern]] with `outside_path=True` so logs land next to the installed exe, not inside the PyInstaller temp.

## Depends on
- [[Logger]]
- [[Resource Path Resolution Pattern]]

## Used by
- [[Bot Entry Point]]

## Gotchas
- Logs older than 7 days are unrecoverable — capture them before reproducing rare issues.

## See also
- [[_index]]
- [[Output Files]]
