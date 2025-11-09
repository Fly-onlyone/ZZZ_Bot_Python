# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ZZZ Bot is a desktop automation tool for the game "Zenless Zone Zero" by HoYoverse. It automates daily tasks on the HoYoLab event website including check-ins, shopping, redemptions, and prize draws, with email notifications.

**Tech Stack:**
- **Backend:** Python (FastAPI, Playwright, OpenCV, Schedule)
- **Frontend:** React 18 + Material-UI v6 + Vite
- **Desktop:** System tray integration (Pystray)
- **Packaging:** PyInstaller + Inno Setup

## Architecture

### Hybrid Desktop Application
- **Development Mode:**
  - Backend: `python src/Bot.py` (FastAPI on port 8000)
  - Frontend: `cd frontend && npm run dev` (Vite dev server on port 3000)
- **Production Mode:**
  - Single executable serving both backend and built frontend on port 8000
  - System tray icon with web UI launcher

### Browser Automation Pipeline
```
Bot.py (scheduler) → playwright_task()
  ├─→ Mission.run()        # Daily missions
  ├─→ ShoppingHandler.run() # Shopping automation
  └─→ DrawHandler.run()     # Prize draws
       ↓
  Save session state → Send email notification
```

### Image Recognition System
Uses OpenCV to detect UI states by comparing screenshots with reference images in `sample/` and `reward image/`:
- Game avatar identification (ZZZ vs other games)
- Button state detection (Finished/Unfinished/Reward)
- Reward recognition from prize draws
- Threshold: <5% difference for matches

Key module: `ImageProcessor.py` with `RetryHelper.py` for element polling.

### Data Persistence
- Base class: `Serializable` with `.save()` and `.load()` methods
- Storage: JSON files in `output/` folder
- Automatic rotation: Keeps last 5 days of mission data, 30 days of redemptions

## Key Modules

### Core Backend (`src/`)
- **Bot.py:** Main entry, scheduler, FastAPI server, system tray
- **GlobalVar.py:** Global config, settings dataclass, shared app instance
- **Mission.py:** Daily mission automation
- **ShoppingHandler.py:** Item shopping and code generation
- **DrawHandler.py:** Prize draw automation
- **RedeemAutofill.py:** Redemption code submission
- **ImageProcessor.py:** OpenCV-based UI detection
- **ManualLogin.py:** Thread-safe manual browser session control
- **DataHandler.py:** JSON serialization utilities
- **Notification.py:** Email reports via Apprise with Jinja2 templates

### Frontend (`frontend/src/`)
- **main.jsx:** React app entry with MUI theme configuration
- **PermanentDrawer.jsx:** Navigation drawer component
- **ValueAdapter.jsx:** Dynamic settings form generator (detects types, renders appropriate inputs)
- **DataLoader.jsx:** API client with TanStack Query integration
- **Overview/Shopping/Redeem/ManualLogin.jsx:** Feature pages

### REST API Endpoints
- `/shopping`, `/redeem`, `/account`, `/settings` - CRUD operations
- `/manual` - Manual browser control (open/close/status)
- `/overview/mission` - Mission reports with date filtering
- `/routes` - Dynamic route listing

## Path Resolution Strategy

Critical for both development and packaged exe:
```python
def resource_path(relative_path, outside=False):
    # Handles paths differently in dev vs exe mode
    # outside=True for output/, screenshot/ (persist across updates)
    # outside=False for bundled resources
```

When testing exe behavior in dev: `set SIMULATE_EXE=1` environment variable.

## Common Commands

### Development
```bash
# Run backend (auto-opens web UI at http://localhost:8000)
python src/Bot.py

# Run frontend dev server
cd frontend
npm install
npm run dev
```

### Build
```bash
# Build frontend
cd frontend
npm run build

# Create executable
cd product
pyinstaller Bot.spec

# Create installer (requires Inno Setup)
iscc installer.iss
```

### Testing
```bash
pytest src/test/
```

## Configuration Files

### `output/settings.json`
```json
{
  "schedule_times": ["08:00", "20:00"],
  "exit_after_run": false,
  "open_web_ui": true,
  "hide_browser": true,
  "run_task": false,
  "gather_shopping_data": true,
  "redeem_after_gather_data": true,
  "buy_all": true,
  "draw_item": true
}
```

### `output/account.json`
Stores email credentials for Gmail notifications.

## Important Patterns

### 1. Session Management
- Playwright stores sessions in `authentication data/`
- First-time setup requires manual login via web UI
- Session persists across runs for automated execution

### 2. Scheduled Tasks
- Uses `schedule` library for time-based execution
- Checks for missed runs on startup
- Tracks last run in `output/last_run.json`
- Next run calculated and displayed in web UI

### 3. Image Comparison Workflow
Instead of fixed selectors (which break easily), the bot:
1. Takes screenshots during execution
2. Compares with reference images using `cv2.matchTemplate`
3. Calculates difference percentage
4. Makes decisions based on visual similarity

This handles dynamic web content and layout changes gracefully.

### 4. React Dynamic Forms
`ValueAdapter.jsx` generates forms from JSON structure:
- Automatically detects types (bool → switch, array → multi-input, string → text field)
- Custom rendering via `typeConfig` prop
- Synchronized with backend via API calls

### 5. PyInstaller Packaging
`Bot.spec` includes:
- Frontend build files (`frontend/dist`)
- Reference images (`sample/`, `reward image/`)
- Playwright browsers (chromium)
- Apprise and Plyer submodules
- Icon and version info

## Module Dependencies

```
Bot.py
  ├─→ GlobalVar (config, FastAPI app)
  ├─→ Mission
  │    ├─→ ImageProcessor
  │    ├─→ RetryHelper
  │    └─→ DataHandler
  ├─→ ShoppingHandler
  │    ├─→ RedeemAutofill
  │    │    └─→ AutoLogin
  │    └─→ ImageProcessor
  ├─→ DrawHandler
  │    ├─→ RedeemAutofill
  │    └─→ ImageProcessor
  ├─→ ManualLogin
  └─→ Notification (Jinja2 templates in src/message/)
```

## Logging

- Uses `TimedRotatingFileHandler` (7-day retention) in `src/logs/`
- Custom `NoImportFilter` to reduce noise
- In exe mode: stdout/stderr redirected to log file

## Code Style Notes

- File paths: Always use `resource_path()` for cross-mode compatibility
- Error handling: Graceful degradation with logging, avoid crashing on missing elements
- API responses: Use Pydantic models for validation
- Frontend state: TanStack Query for server state, React state for UI state
- Image comparison: Always use absolute paths for OpenCV, log comparison percentages
