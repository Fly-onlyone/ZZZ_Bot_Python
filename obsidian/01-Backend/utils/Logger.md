---
tags: [backend, utils]
---

# Logger

> Two small logging helpers: a stream-to-logger redirector that preserves partial lines, and an import-noise filter.

## Source
- `backend/utils/Logger.py` — primary

## How it works
- `StreamToLogger(logger, level)` — file-like object meant to replace `sys.stdout` / `sys.stderr` in packaged exe mode (where the console is detached). It buffers writes in `self._buffer` and only emits when it sees `\n`, so partial writes from `print(..., end="")` or libraries that flush byte-at-a-time do NOT produce one log line per character. `flush()` emits any trailing buffered text. This is what lets `print` calls inside the bundled binary still land in `app.log`.
- `NoImportFilter(logging.Filter)` — drops any record whose message contains the literal string `"Importing"`. Cuts boilerplate noise from Playwright and other libraries during startup so the log stays focused on actual run events.

Both are wired up in [[Bot Entry Point]] when configuring the `TimedRotatingFileHandler` (7-day retention) under `backend/logs/app.log` (dev) or the exe-side resolved path.

## Depends on
- *(stdlib `logging` only)*

## Used by
- [[Bot Entry Point]] — log setup
- [[Health Endpoints]] — `/logs` parses the output

## See also
- [[_index]]
- [[Logging Setup]]
