---
tags: [operations]
---

# Bot Dev Run

> `uv sync && uv run python backend/Bot.py` — syncs the Python env, boots FastAPI on 8001, and auto-launches the Vite dev frontend at `http://localhost:3000`.

## Source
- `backend/Bot.py`
- `pyproject.toml`

## How it works
`uv sync` reads `pyproject.toml` / `uv.lock` and provisions a `.venv/` with all deps including Playwright. `uv run python backend/Bot.py` then:

1. Bootstraps logging via [[Logger]] to `backend/logs/`.
2. Initialises [[GlobalVar]] (FastAPI app, scheduler, browser service).
3. Starts Uvicorn on port 8001.
4. Spawns the Vite dev server (port 3000) and opens it in the default browser.
5. Registers the schedule from `output/settings.json` so the [[Daily Task Cycle]] fires at the configured times.

Pass `--no-frontend` to skip the Vite spawn (useful when [[Tauri Dev Run]] is driving the UI).

## Depends on
- [[uv]]
- [[Bot Entry Point]]
- [[Frontend Env Resolver]]

## Used by
- [[Dev Server Architecture]]

## See also
- [[_index]]
- [[Tauri Dev Run]]
- [[Port Configuration]]
