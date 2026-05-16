---
tags: [backend, api]
---

# Account Endpoints

> Email-credential CRUD plus the manual-browser control endpoint that pilots [[ManualLoginManager]].

## Source
- `backend/api/routes.py` — primary

## How it works
- `GET /account` calls `ensure_accounts_loaded()` and returns the `accounts` dataclass via `asdict`.
- `POST /account` merges incoming fields into the in-memory `accounts` singleton (only known attributes), then persists via `MongoRepository.save_account()`.
- `POST /manual` is the manual-login state machine: it accepts `{url, playState}`. When `playState` is truthy and no session is running, it calls `manager.start_session(url)` and schedules the actual Playwright work via `BackgroundTasks.add_task(run, url)`. When falsy, it calls `manager.stop_session()`. Each branch returns `{message, success, state}` where `state` is the current `ManualLoginState` value.

## Depends on
- [[GlobalVar]] — `accounts`, `ensure_accounts_loaded`
- [[MongoRepository]] — `save_account`
- [[ManualLoginManager]] — `/manual` state transitions

## Used by
- [[Account Page]] — credential form
- [[Manual Login Page]] — `/manual`

## See also
- [[_index]]
- [[Manual Login Flow]]
