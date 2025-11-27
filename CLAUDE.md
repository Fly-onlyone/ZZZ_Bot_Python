# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ZZZ Bot is a desktop automation tool for the game "Zenless Zone Zero" by HoYoverse. It automates daily tasks on the
HoYoLab event website including check-ins, shopping, redemptions, and prize draws, with email notifications.

**Tech Stack:**

- **Backend:** Python (FastAPI, Playwright, OpenCV, Schedule)
- **Frontend:** React 18 + Material-UI v6 + Vite
- **Desktop:** System tray integration (Pystray)
- **Packaging:** PyInstaller + Inno Setup

## Architecture

### Hybrid Desktop Application

- **Development Mode:**
    - Backend: `python backend/Bot.py` (FastAPI on port 8000)
    - Frontend: `cd frontend && npm run dev` (Vite dev server on port 3000)
- **Production Mode:**
    - Single executable serving both backend and built frontend on port 8000
    - System tray icon with web UI launcher

### Browser Automation Pipeline

```
Bot.py (scheduler) → playwright_task()
  ├─→ MissionHandler.run()        # Daily missions
  ├─→ ShoppingHandler.run()       # Shopping automation
  ├─→ DrawHandler.run()           # Prize draws
  └─→ HuntModeHandler.run_hunt()  # Hunt mode (timed item purchases)
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

### Core Backend (`backend/`)

The backend follows a layered architecture with clear separation of concerns:

**Core (`backend/core/`):**

- **Bot.py:** Main entry, scheduler, FastAPI server, system tray
- **GlobalVar.py:** Global config, settings dataclass, shared app instance
- **ManualLogin.py:** Thread-safe manual browser session control
- **Notification.py:** Email reports via Apprise with Jinja2 templates
- **constants.py:** Application constants

**Handlers (`backend/handlers/`):**

- **MissionHandler.py:** Daily mission automation
- **ShoppingHandler.py:** Item shopping and code generation
- **DrawHandler.py:** Prize draw automation
- **HuntModeHandler.py:** Automated item purchasing when shop renews

**Automation (`backend/automation/`):**

- **ImageProcessor.py:** OpenCV-based UI detection
- **RedeemAutofill.py:** Redemption code submission
- **AutoLogin.py:** Automated login handling
- **RetryHelper.py:** Element polling and retry logic
- **Selectors.py:** Web element selectors

**Services (`backend/services/`):**

- **BrowserService.py:** Browser management and session handling

**Repositories (`backend/repositories/`):**

- **DataRepository.py:** Data persistence layer

**Strategies (`backend/strategies/`):**

- **ImageComparisonStrategy.py:** Image matching algorithms

**Domain (`backend/domain/`):**

- **models.py:** Domain models and data classes

**API (`backend/api/`):**

- **routes.py:** REST API endpoint definitions

**Utils (`backend/utils/`):**

- **DataHandler.py:** JSON serialization utilities
- **Logger.py:** Logging configuration
- **NotificationHelper.py:** Desktop notification helper
- **StringUtil.py:** String manipulation utilities
- **Win32Icon.py:** Windows icon handling

### Frontend (`frontend/src/`)

The frontend follows a modular component architecture:

**Entry Point:**

- **main.jsx:** React app entry with MUI theme configuration

**Pages (`pages/`):**

- **Overview.jsx:** Dashboard with mission reports and hunt status
- **Shopping.jsx:** Shopping management with hunt mode configuration
- **Redeem.jsx:** Redemption code management
- **ManualLogin.jsx:** Manual login interface
- **index.js:** Page exports

**Components:**

- **common/** - Shared components (SaveButton)
- **layout/** - Layout components (AppHeader, NavigationDrawer)
- **forms/** - Form utilities (ValueAdapter - dynamic form generator)
- **fields/** - Field components (ArrayField, BooleanField, SelectField, TextField)
- **index.js:** Component exports

**Routes (`routes/`):**

- **PermanentDrawer.jsx:** Main navigation and routing component

**Content (`content/`):**

- **Mission.jsx:** Mission history and reports
- **Hunt.jsx:** Hunt mode status and next scheduled hunt
- **RunningStatus.jsx:** Real-time bot status display

**Services (`services/`):**

- **DataLoader.jsx:** API client with TanStack Query integration
- **index.js:** Service exports

**Hooks (`hooks/`):**

- **useFormState.js:** Form state management
- **useShoppingState.js:** Shopping data state management
- **usePriorityManagement.js:** Item priority handling
- **useFieldRenderer.jsx:** Dynamic field rendering
- **index.js:** Hook exports

**Theme (`theme/`):**

- **muiTheme.js:** Material-UI theme configuration
- **ThemeContext.jsx:** Theme context provider
- **colors.js:** Color palette definitions
- **themes.js:** Theme variants
- **styles.js:** Common styles

**Config (`config/`):**

- **constants.js:** Frontend constants
- **index.js:** Config exports

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
```

When testing exe behavior in dev: `set SIMULATE_EXE=1` environment variable.

## Common Commands

### Development

```bash
# Run backend (auto-opens web UI at http://localhost:8000)
python backend/Bot.py

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
pytest backend/test/
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
  "enable_hunt_mode": true
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

`components/forms/ValueAdapter.jsx` generates forms from JSON structure:

- Automatically detects types (bool → switch, array → multi-input, string → text field)
- Custom rendering via `typeConfig` prop
- Synchronized with backend via API calls

### 5. Hunt Mode

Hunt Mode automates purchasing specific items when the shop renews. Key features:

**Workflow:**

1. User marks items for "hunting" in the Shopping page
2. Bot calculates next hunt time based on item availability
3. Bot opens shopping screen 2 minutes before item becomes available
4. Polls item button every second, waiting for "Exchange" status
5. Exchanges all hunt items and collects redemption codes
6. Redeems all codes after exchanges complete
7. Removes successfully hunted items from hunt list

**Implementation Details:**

- Priority-based: Items are hunted in the order they appear in the Selected list
- Two-phase execution: Exchange all items first, then redeem all codes
- Automatic cleanup: Successfully hunted items are removed from hunt list
- Visual monitoring: Logs button status changes during polling
- Configurable timeouts: Max 3-minute wait per item
- Desktop notifications: Reports hunt results with success/failure counts

**Key Functions:**

- `get_hunt_items()` - Returns hunt items sorted by shopping priority
- `get_next_hunt_time()` - Calculates earliest item availability time
- `wait_for_exchange_button()` - Polls item until Exchange button appears
- `exchange_item_only()` - Exchanges item without immediate redemption
- `redeem_all_codes()` - Bulk redeems all collected codes
- `run_hunt()` - Main hunt mode orchestrator

### 6. PyInstaller Packaging

`Bot.spec` includes:

- Frontend build files (`frontend/dist`)
- Reference images (`sample/`, `reward image/`)
- Playwright browsers (chromium)
- Apprise and Plyer submodules
- Icon and version info

## Module Dependencies

```
Bot.py (core/)
  ├─→ GlobalVar (core/, config, FastAPI app)
  ├─→ ManualLogin (core/)
  ├─→ Notification (core/, Jinja2 templates in backend/message/)
  ├─→ MissionHandler (handlers/)
  │    ├─→ ImageProcessor (automation/)
  │    ├─→ RetryHelper (automation/)
  │    └─→ DataHandler (utils/)
  ├─→ ShoppingHandler (handlers/)
  │    ├─→ RedeemAutofill (automation/)
  │    │    └─→ AutoLogin (automation/)
  │    ├─→ ImageProcessor (automation/)
  │    └─→ DataHandler (utils/)
  ├─→ DrawHandler (handlers/)
  │    ├─→ RedeemAutofill (automation/)
  │    ├─→ ImageProcessor (automation/)
  │    └─→ DataHandler (utils/)
  └─→ HuntModeHandler (handlers/)
       ├─→ ShoppingHandler (handlers/)
       ├─→ RedeemAutofill (automation/)
       ├─→ ImageProcessor (automation/)
       ├─→ RetryHelper (automation/)
       ├─→ DataHandler (utils/)
       ├─→ NotificationHelper (utils/)
       └─→ StringUtil (utils/)
```

## Logging

- Uses `TimedRotatingFileHandler` (7-day retention) in `backend/logs/`
- Custom `NoImportFilter` to reduce noise
- In exe mode: stdout/stderr redirected to log file

## Code Style Notes

- **File paths:** Always use `resource_path()` for cross-mode compatibility
- **Error handling:** Graceful degradation with logging, avoid crashing on missing elements
- **API responses:** Use Pydantic models for validation
- **Backend architecture:** Follow layered structure - handlers use services/automation, utilities remain isolated
- **Frontend organization:** Use barrel exports (index.js) for clean imports, keep components modular
- **Frontend state:** TanStack Query for server state, React state for UI state
- **Image comparison:** Always use absolute paths for OpenCV, log comparison percentages
- **Hunt mode:** Always use two-phase execution (exchange all, then redeem all) to avoid session issues

## Commit Message Style

When writing commit messages for this project, follow these guidelines:

- **Keep it short and concise** - Brief, action-oriented statements
- **Use simple present tense** - "Add", "Fix", "Improve", not "Added" or "Adding"
- **Multiple changes** - Separate with periods, list main changes only
- **Focus on what, not why** - Describe the change, not the reason
- **No detailed explanations** - Save details for PR descriptions

**Examples:**

- `Add hunt overview. Fix countdown regex. Improve hunt scheduling. Fix icon colors.`
- `Add hunt mode`
- `Fix draw handler`
- `Improve codebase`

**Format:** `[Verb] [brief description]. [Verb] [brief description]. ...`
