---
tags: [integration]
---

# uv

> Astral's Rust-based Python package + project manager; replaces pip/poetry for installing deps, running scripts, and managing the virtual env.

## Used for
- `uv sync` — install backend deps + create `.venv`
- `uv run python backend/Bot.py` — run the dev backend
- `uv run --group dev pytest backend/test/` — run tests
- `uv run --group dev pyinstaller product/BotSidecar.spec` — build the sidecar (called from [[Prepare Tauri Sidecar Script]])

## Configuration
- `pyproject.toml` — `[project]` deps + `[dependency-groups.dev]` group
- `[tool.uv]` `default-groups = []` — dev tools (pytest, pyinstaller, pillow) must be explicitly requested via `--group dev`
- Requires Python `>=3.11`

## Wire-up
- `pyproject.toml` — manifest
- `uv.lock` — lockfile (not shown)
- `frontend/scripts/prepare-tauri-sidecar.ts` — invokes `uv run --group dev pyinstaller`

## Auth mode
N/A

## See also
- [[_index]]
- [[PyInstaller]]
- [[Bot Dev Run]]
