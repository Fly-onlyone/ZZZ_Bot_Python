# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ZZZ Bot is a desktop automation tool for the game "Zenless Zone Zero" by HoYoverse. It automates daily tasks on the
HoYoLab event website including check-ins, shopping, redemptions, and prize draws, with email notifications.

**Tech Stack:**

- **Backend:** Python (FastAPI, Playwright, OpenCV, Schedule)
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
| `repositories/` | Data persistence (JSON + MongoDB)                  |
| `domain/`       | Data models                                        |
| `api/`          | REST endpoint definitions                          |
| `utils/`        | Helpers (logging, data handling, strings)          |
| `strategies/`   | Strategy patterns (image comparison)               |
| `message/`      | Email templates (Jinja2)                           |

### Frontend (`frontend/src/`)

| Directory     | Purpose                                                    |
|---------------|------------------------------------------------------------|
| `pages/`      | Route components (Overview, Shopping, Redeem, ManualLogin) |
| `components/` | UI components (common, layout, forms, fields)              |
| `content/`    | Page sections (Mission, Hunt, RunningStatus)               |
| `hooks/`      | Custom hooks (form state, shopping state)                  |
| `services/`   | API client with TanStack Query                             |
| `theme/`      | Theme system (4 themes: Nebula, Venom, Glacier, Cyber)     |
| `config/`     | Frontend constants                                         |
| `routes/`     | Route configuration and drawer                             |

### REST API Endpoints

- `/shopping`, `/redeem`, `/account`, `/settings` - CRUD operations
- `/manual` - Manual browser control (open/close/status)
- `/overview/mission` - Mission reports with date filtering
- `/overview/hunt` - Hunt mode status and next scheduled hunt time
- `/routes` - Dynamic route listing

## Path Resolution Strategy

Critical for both development and packaged exe:

```python
def resource_path(relative_path, outside=False):
    # Handles paths differently in dev vs exe mode
    # outside=True for output/, screenshot/ (persist across updates)
    # outside=False for bundled resources
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

## Configuration Files

### `output/settings.json`

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

### `output/account.json`

Stores email credentials for Gmail notifications.

### `output/shopping.json`

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

| Context | Backend | Frontend |
|---------|---------|----------|
| Dev (`uv run python backend/Bot.py`) | **8001** | 3000 (Vite, started by Bot.py) |
| `tauri dev` | **8001** (start `Bot.py --no-frontend` manually; set `ZZZ_DEV_BACKEND_PORT=8001`) | 3000 (Vite, started manually) |
| Production exe (Tauri sidecar) | **8000** | Tauri WebView (serves `frontend/dist`) |

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
