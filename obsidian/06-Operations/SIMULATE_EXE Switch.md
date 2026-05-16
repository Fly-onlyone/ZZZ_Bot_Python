---
tags: [operations]
---

# SIMULATE_EXE Switch

> Setting `SIMULATE_EXE=1` forces `resource_path()` to behave as if it were running inside the PyInstaller exe, so you can reproduce exe-only path bugs from a dev terminal.

## Source
- `backend/utils/` — `resource_path()` checks `os.environ["SIMULATE_EXE"]` alongside `sys.frozen`

## How it works
`resource_path()` normally picks the dev branch in development (paths relative to the repo root) and the exe branch when `sys.frozen` is set by PyInstaller. `SIMULATE_EXE=1` short-circuits the check so the exe branch fires even in dev — useful for reproducing path bugs that only show up in the packaged build.

```cmd
set SIMULATE_EXE=1
uv run python backend/Bot.py
```

The flag does not change anything else (no console-redirect, no PyInstaller bundle extraction). It only affects path resolution.

## Depends on
- [[Resource Path Resolution Pattern]]

## Used by
- [[Bot Dev Run]]

## Gotchas
- Forgetting to `set SIMULATE_EXE=` (empty) leaves it on for the rest of the shell session.
- Doesn't simulate stdout redirection — log behaviour still matches dev mode.

## See also
- [[_index]]
- [[Output Files]]
