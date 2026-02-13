# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Last Synced Commit:** `07562c2` (2025-01-12)

## Project Overview

ZZZ Bot is a desktop automation tool for the game "Zenless Zone Zero" by HoYoverse. It automates daily tasks on the
HoYoLab event website including check-ins, shopping, redemptions, and prize draws, with email notifications.

**Tech Stack:**

- **Backend:** Python (FastAPI, Playwright, OpenCV, Schedule)
- **Frontend:** React 18 + Material-UI v6 + Vite
- **Desktop:** System tray integration (Pystray)
- **Packaging:** PyInstaller + Inno Setup

**Frontend Dependencies:**

- `@mui/material@^6.1.8` - Material UI components
- `@mui/x-data-grid@^7.23.0` - Data grid for tables
- `@mui/x-date-pickers@^7.22.3` - Date/time pickers
- `@tabler/icons-react@^3.24.0` - Icon library
- `@tanstack/react-query@^5.62.3` - Server state management
- `framer-motion@^12.23.24` - Animation library
- `react-router-dom@^7.0.0` - Routing
- `dayjs@^1.11.13` - Date manipulation

## Key Modules

### Backend (`backend/`)

| Directory       | Purpose                                            |
|-----------------|----------------------------------------------------|
| `core/`         | App entry, scheduler, config, notifications        |
| `handlers/`     | Task orchestration (Mission, Shopping, Draw, Hunt) |
| `automation/`   | Browser interaction, image recognition             |
| `services/`     | Browser lifecycle management                       |
| `repositories/` | Data persistence                                   |
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

See `.claude/rules/architecture.md` for detailed file listings and module dependencies.

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
# Sync Python environment and run backend (auto-opens web UI at http://localhost:8000)
uv sync
uv run python backend/Bot.py

# Run frontend dev server
cd frontend
bun install
bun run dev
```

### Build

```bash
# Build frontend
cd frontend
bun run build

# Sync build dependencies
uv sync --group dev

# Create executable
cd product
uv run pyinstaller Bot.spec

# Create installer (requires Inno Setup)
iscc installer.iss
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
  "open_web_ui": true,
  "hide_browser": true,
  "run_task": false,
  "gather_shopping_data": true,
  "exchange_good": true,
  "buy_all": true,
  "draw_item": true,
  "enable_hunt_mode": true,
  "stop_on_failed_exchange": true,
  "theme": "nebula"
}
```

### `output/account.json`

Stores email credentials for Gmail notifications.

### `output/shopping.json`

Stores shopping data including item selection and hunt mode configuration:

```json
{
  "Selected": [
    "Item 1",
    "Item 2",
    "Item 3"
  ],
  "Hunt": [
    "Item 2"
  ],
  "Item's list": {
    "Item 1": {
      "Available": "Yes",
      "Point": 100
    },
    "Item 2": {
      "Available": "14:30 20/01/25",
      "Point": 150
    }
  }
}
```

- **Selected:** Items to purchase, ordered by priority
- **Hunt:** Items to hunt when shop renews (subset of Selected)
- **Item's list:** Item details including availability and cost

## Logging

- Uses `TimedRotatingFileHandler` (7-day retention) in `backend/logs/`
- Custom `NoImportFilter` to reduce noise
- In exe mode: stdout/stderr redirected to log file

## Documentation

Detailed guidelines are in `.claude/rules/`:

- `architecture.md` - System architecture and design decisions
- `code-guide.md` - Naming conventions, code patterns, and animation guidelines
- `documentation-style.md` - Documentation guidelines

Custom commands are in `.claude/commands/`:

- `commit.md` - Git commit message style (`/commit`)

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
