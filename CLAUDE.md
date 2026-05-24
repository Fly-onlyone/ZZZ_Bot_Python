# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Documentation lives in [`obsidian/`](./obsidian/_HOME.md) — open as an Obsidian vault, or browse the markdown directly. Start at `_HOME.md` for reading paths.

## Project Overview

ZZZ Bot is a desktop automation tool for the game "Zenless Zone Zero" by HoYoverse. It automates daily tasks on the
HoYoLab event website including check-ins, shopping, redemptions, and prize draws, with email notifications.

**Tech Stack:**

- **Backend:** Python (FastAPI, Playwright, OpenCV, Schedule, embedded SQLite)
- **Frontend:** React 18 + Material-UI v6 + Vite
- **Desktop:** Tauri desktop shell with native tray icon + Python sidecar backend
- **Packaging:** Tauri (NSIS) + Python sidecar (PyInstaller)

## Key Modules

### Backend (`backend/`)

| Directory       | Purpose                                            |
|-----------------|----------------------------------------------------|
| `core/`         | App entry, scheduler, config, notifications        |
| `handlers/`     | Task orchestration (Mission, Shopping, Draw, Hunt) |
| `automation/`   | Browser interaction, image recognition             |
| `services/`     | Browser lifecycle management                       |
| `repositories/` | Data persistence (embedded SQLite)                 |
| `domain/`       | Data models                                        |
| `api/`          | REST endpoint definitions                          |
| `utils/`        | Helpers (logging, data handling, strings)          |
| `strategies/`   | Strategy patterns (image comparison)               |
| `message/`      | Email templates (Jinja2)                           |

### Frontend (`frontend/src/`)

| Directory     | Purpose                                                                    |
|---------------|----------------------------------------------------------------------------|
| `pages/`      | Route components (Overview, Shopping, Redeem, ManualLogin, LocatorTracker) |
| `components/` | UI components (common, layout, forms, fields)                              |
| `content/`    | Page sections (Mission, Hunt, RunningStatus)                               |
| `hooks/`      | Custom hooks (form state, shopping state)                                  |
| `services/`   | API client with TanStack Query                                             |
| `theme/`      | Theme system (4 themes: Nebula, Venom, Glacier, Cyber)                     |
| `config/`     | Frontend constants                                                         |
| `routes/`     | Route configuration and drawer                                             |

### REST API Endpoints

- `/shopping`, `/redeem`, `/account`, `/settings` - CRUD operations
- `/manual` - Manual browser control (open/close/status)
- `/overview/mission` - Mission reports with date filtering
- `/overview/hunt` - Hunt mode status and next scheduled hunt time
- `/locator-tracker` - Locator interaction telemetry (GET list, POST clear)
- `/routes` - Dynamic route listing

## Path Resolution Strategy

Critical for both development and packaged exe:

```python
def resource_path(relative_path, outside_path=False):
    # Handles paths differently in dev vs exe mode
    # outside_path=True for output/, screenshot/ (persist across updates)
    # outside_path=False for bundled resources
    pass
```

When testing exe behavior in dev: `set SIMULATE_EXE=1` environment variable.

## Common Commands

### Development

```bash
# Sync Python environment and run backend (port 8001, auto-opens web UI at http://localhost:3000)
uv sync
uv run python backend/Bot.py

# Run frontend dev server
cd frontend
bun install
bun run dev
```

### Build

```bash
# Build frontend and sidecar
cd frontend
bun run build
bun run tauri:prepare-sidecar

# Build Windows installer bundle (NSIS)
cd ..
cargo tauri build
```

### Testing

```bash
uv run --group dev pytest backend/test/
```

## CI/CD

GitHub Actions workflows live in `.github/`. The repository's **default branch is `dev`**
(not `main`) — Dependabot, CodeQL, and release-please all read their state from the default
branch, so they activate once these files land on `dev`.

| File                            | Trigger                                | Purpose                                                                   |
|---------------------------------|----------------------------------------|---------------------------------------------------------------------------|
| `.github/workflows/ci.yml`      | push/PR to `main`, `dev`               | `pytest` (Windows) + frontend build; Ruff and ESLint/Prettier lint (Linux) |
| `.github/workflows/codeql.yml`  | push/PR to `main`, `dev` + weekly cron | CodeQL static analysis for Python + JS/TS                                  |
| `.github/workflows/release.yml` | push to `dev`                          | release-please Release PR; builds the NSIS installer when a release is cut |
| `.github/dependabot.yml`        | weekly                                 | Grouped update PRs for `uv`, `bun`, `cargo`, `github-actions`              |

- Backend tests run on `windows-latest` to match the only shipping target (winotify, NSIS);
  lint jobs run on `ubuntu-latest` (OS-agnostic, cheaper).

**Lint/format:** Python uses **Ruff** — `uv run ruff check backend/` + `uv run ruff format
backend/`, config in `pyproject.toml` `[tool.ruff]`. Frontend uses **ESLint**
(`frontend/eslint.config.js`) + **Prettier** (`frontend/.prettierrc.json`) — `bun run lint`
and `bun run format:check`.

**Releases (release-please):** Commit to `dev` with Conventional Commits (`feat:`, `fix:`…).
release-please maintains a "Release PR" that bumps the version in `tauri.conf.json`,
`Cargo.toml`, and `pyproject.toml` and updates `CHANGELOG.md`. Merging that PR tags
`vX.Y.Z`, creates the GitHub Release, and triggers the Windows installer build, which
attaches the NSIS `.exe` to the release.

## Stored Documents

These documents live as rows in the SQLite database (see Data Storage), not as files. The
shapes below are what `DataStore` reads and writes.

### `settings`

```json
{
  "schedule_times": [
    "08:00",
    "20:00"
  ],
  "exit_after_run": false,
  "hide_browser": true,
  "enable_hunt_mode": true,
  "theme": "nebula"
}
```

> Additional advanced settings (hunt polling, window state, task toggles) are managed via the Settings page.

### `account`

Stores email credentials for Gmail notifications.

### `shopping`

```json
{
  "Selected": [
    "Item 1",
    "Item 2"
  ],
  "Hunt": [
    "Item 2"
  ],
  "Item's list": {
    "Item 1": {
      "Available": "Yes",
      "Point": 100
    }
  }
}
```

- **Selected:** Items to purchase, ordered by priority
- **Hunt:** Items to hunt when shop renews (subset of Selected)
- **Item's list:** Item details including availability and cost

## Port Configuration

Dev and production use **different ports** to avoid conflicts when both run simultaneously.

| Context                              | Backend                                                                           | Frontend                               |
|--------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------|
| Dev (`uv run python backend/Bot.py`) | **8001**                                                                          | 3000 (Vite, started by Bot.py)         |
| `tauri dev`                          | **8001** (start `Bot.py --no-frontend` manually; set `ZZZ_DEV_BACKEND_PORT=8001`) | 3000 (Vite, started manually)          |
| Production exe (Tauri sidecar)       | **8000**                                                                          | Tauri WebView (serves `frontend/dist`) |

**How `VITE_BACKEND_URL` resolves:**

- `bun run dev` → reads `frontend/.env.development` → `http://127.0.0.1:8001`
- `bun run build` → `.env.development` not loaded → falls back to `http://127.0.0.1:8000` constant in `constants.js`

**Key files:**

- `backend/Bot.py` — `--port` default is **8001**
- `frontend/.env.development` — sets `VITE_BACKEND_URL=http://127.0.0.1:8001`
- `frontend/src/config/constants.js` — fallback `BACKEND_URL` is `http://127.0.0.1:8000` (production)
- `src-tauri/src/lib.rs` — `backend_port()` defaults to **8000**; override with `ZZZ_DEV_BACKEND_PORT`

## Logging

- Uses `TimedRotatingFileHandler` (7-day retention) in `backend/logs/`
- Custom `NoImportFilter` to reduce noise
- In exe mode: stdout/stderr redirected to log file

## Locator Tracker

Centralized telemetry for every Playwright locator interaction across all handlers. Lives in
`backend/automation/LocatorTracker.py`.

- **Dedup key:** `locator:<md5(selector)[:12]>` — one SQLite row per unique selector
- **Screenshots:** Full-page on every failure; throttled (1hr) on success. Element-level crop when a `Locator` object is
  available.
- **DOM snapshots:** Captured as binary assets on failure only
- **Storage:** `locator_tracker` table; rows carry an `expires_at` column purged after 7 days
- **Instrumented modules:** `EventNavigator`, `RetryHelper`, `MissionHandler`, `ShoppingHandler`, `DrawHandler`,
  `HuntModeHandler`
- **Frontend:** Tools > Locator tab — filterable table with page + element screenshot thumbnails

When adding new locator interactions, call `track_locator()` or use the handler-local `_safe_track()` wrapper. Always
pass `locator=` kwarg when a `Locator` object is available for element-level screenshots.

## Data Storage

All runtime data lives in a single embedded **SQLite** database — no separate database
service to install. The file is created on first launch under `data/` (`zzz_bot_dev.db` in
dev, `zzz_bot.db` in the packaged exe, resolved with `outside_path=True` so it survives
updates).

- `backend/repositories/DataStore.py` — flat module of functions over SQLite; single-doc
  collections share a `documents` key-value table, `missions` / `redemptions` /
  `locator_tracker` / `binary_assets` get dedicated tables.
- `backend/repositories/connection.py` — shared `sqlite3` connection (WAL, `check_same_thread=False`,
  one `RLock` serializes access — the backend is multi-threaded).
- **TTL:** MongoDB TTL indexes are gone; rows carry an `expires_at` column and
  `purge_expired()` sweeps them at startup and (throttled) before TTL-collection reads —
  missions 5 days, redemptions 30 days, locator telemetry 7 days.
- **Migration:** the one-time Mongo → SQLite copy is exposed two ways, both calling the
  same `migrate()` function in `backend/utils/migrate_mongo_to_sqlite.py`:
  - **In-app** — **Backup → Maintenance → Migrate from MongoDB** (POST `/maintenance/mongo-migration`).
    On success the endpoint hot-loads settings / account / shopping via
    `_refresh_runtime_state_after_restore`.
  - **CLI** — `uv run python backend/utils/migrate_mongo_to_sqlite.py` (optional
    `--mongo-uri` / `--mongo-db`). `pymongo` ships in main runtime deps so both paths work
    out of the box; it is only imported lazily when the migration is actually invoked.

## Data Backup

Data is backed up and restored via the `/backup/export` and `/backup/import` endpoints. The
backup system in `DataStore.py` categorizes collections into two types:

- **Single-doc collections:** `settings`, `account`, `shopping`, `last_run` — one document each
- **Multi-doc collections:** `missions`, `redemptions` — arrays of documents

All collections are listed in `_SINGLE_DOC_COLLECTIONS` and `_MULTI_DOC_COLLECTIONS`. When adding a new
collection, add its name to the appropriate set so it is included in backup export/import and the backup summary page.
Ephemeral locator telemetry is intentionally excluded from backups.

**Key files:**

- `backend/repositories/DataStore.py` — `export_all_data()`, `import_data()`, collection sets
- `backend/api/routes.py` — `/backup/*` endpoints (export, import, summary, config, browse)
- `frontend/src/pages/BackupPage.jsx` — UI for selective backup/restore

## Context7 Library IDs

For documentation lookup via Context7 MCP:

| Library                       | Context7 ID                    |
|-------------------------------|--------------------------------|
| React                         | `/facebook/react`              |
| MUI (Material UI)             | `/mui/material-ui`             |
| MUI X (DataGrid, DatePickers) | `/mui/mui-x`                   |
| Framer Motion                 | `/motiondivision/motion`       |
| FastAPI                       | `/websites/fastapi_tiangolo`   |
| Playwright Python             | `/microsoft/playwright-python` |
| TanStack Query                | `/tanstack/query`              |
