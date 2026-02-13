# Architecture Patterns

## Project Structure

ZZZ Bot follows a hybrid desktop application architecture with clear separation between backend automation and frontend
UI.

### Hybrid Desktop Application

- **Development Mode:**
    - Backend: `python backend/Bot.py` (FastAPI on port 8000)
    - Frontend: `cd frontend && bun run dev` (Vite dev server on port 3000)
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

### Layered Backend Architecture

```
Presentation Layer (FastAPI)
    ↓
Business Logic Layer (Handlers)
    ↓
Automation Layer (Browser interaction, Image recognition)
    ↓
Service Layer (Browser service, External APIs)
    ↓
Data Access Layer (Repositories)
```

**Dependency Flow:** Higher layers depend on lower layers, never the reverse.

### Backend Modules

#### Core (`backend/core/`)

- **Purpose:** Application bootstrapping, global state, notifications
- **Key files:** `Bot.py` (entry point), `GlobalVar.py` (config), `Notification.py` (email)
- **Pattern:** Singleton-like global state, minimal dependencies

#### Handlers (`backend/handlers/`)

- **Purpose:** Business logic orchestration for each task type
- **Files:** `MissionHandler.py`, `ShoppingHandler.py`, `DrawHandler.py`, `HuntModeHandler.py`
- **Pattern:** Task-specific handlers with `run()` method, use automation modules
- **Dependencies:** Automation, Services, Repositories

#### Automation (`backend/automation/`)

- **Purpose:** Browser interaction primitives
- **Files:** `ImageProcessor.py`, `RedeemAutofill.py`, `AutoLogin.py`, `RetryHelper.py`, `Selectors.py`
- **Pattern:** Focused utilities, no business logic
- **Dependencies:** Playwright, OpenCV

#### Services (`backend/services/`)

- **Purpose:** External system integration
- **Files:** `BrowserService.py`
- **Pattern:** Stateful service classes managing lifecycle
- **Dependencies:** Playwright

#### Repositories (`backend/repositories/`)

- **Purpose:** Data persistence abstraction
- **Files:** `DataRepository.py`
- **Pattern:** Repository pattern, returns domain models
- **Dependencies:** Domain models, utils

#### Domain (`backend/domain/`)

- **Purpose:** Core data structures
- **Files:** `models.py`
- **Pattern:** Pydantic models, no logic

#### Utils (`backend/utils/`)

- **Purpose:** Cross-cutting utilities
- **Files:** `DataHandler.py`, `Logger.py`, `StringUtil.py`
- **Pattern:** Stateless helper functions
- **Dependencies:** None (or minimal)

### Frontend Component Organization

```
pages/                 # Route-level components (Overview, Shopping, Redeem)
  ↓
components/            # Reusable UI components
  ├── common/          # Generic components (SaveButton, SectionCard)
  ├── layout/          # Layout components (AppHeader, NavigationDrawer)
  ├── forms/           # Form utilities (ValueAdapter - dynamic form generator)
  └── fields/          # Field components (ArrayField, BooleanField)
  ↓
content/               # Page section components (Mission, Hunt, RunningStatus)
  ↓
hooks/                 # Custom React hooks (useFormState, useShoppingState)
  ↓
services/              # API client (DataLoader with TanStack Query)
  ↓
theme/                 # Theme system (ThemeContext, themes, colors)
```

**Pattern:** Container/Presentational component pattern, state lifted to appropriate level.

## Key Design Decisions

### 1. Path Resolution Strategy

**Problem:** Application runs in two modes (development and packaged exe) with different path structures.

**Solution:** `resource_path(relative_path, outside=False)` function:

- `outside=False`: Bundled resources (images, templates) - uses `_MEIPASS` in exe mode
- `outside=True`: User data (output/, screenshot/) - always uses app directory

**Why:** Ensures consistent file access across development and production.

### 2. Image Recognition vs. Selectors

**Problem:** Web UI selectors break frequently due to dynamic content and updates.

**Solution:** OpenCV template matching with reference images.

**Workflow:**

1. Take screenshot of current state
2. Compare with reference images using `cv2.matchTemplate`
3. Calculate difference percentage
4. Make decisions based on visual similarity (<5% threshold)

**Trade-offs:**

- **Pros:** Resilient to layout changes, works with dynamic content
- **Cons:** Requires reference images, sensitive to UI theme changes

### 3. Session Management

**Problem:** Repeated logins are slow and may trigger security checks.

**Solution:** Persistent Playwright browser context.

**Implementation:**

- Store session in `authentication data/` directory
- First-time setup via manual login UI
- Reuse session across runs

**Why:** Faster execution, avoids repeated authentication flows.

### 4. Hunt Mode Three-Phase Execution

**Problem:** Sequential exchange-and-redeem operations risk session timeout.

**Solution:** Execute hunt in three phases.

**Workflow:**

```python
# Phase 1: Exchange all items (collect codes)
for item in hunt_items:
    exchange_item_only(item)

# Phase 2: Bulk redeem all codes
redeem_all_codes()

# Phase 3: Cleanup hunt list
remove_successful_items()
```

**Why:** Reduces session time, improves reliability, ensures cleanup.

### 5. Dynamic Form Generation

**Problem:** Frontend needs to render forms for various data structures without hardcoding each field.

**Solution:** `ValueAdapter` component with type detection.

**Pattern:**

```jsx
<ValueAdapter
  label="Settings"
  value={data}
  onChange={handleChange}
  typeConfig={customRenderers}
/>
```

**How it works:**

- Detects type (bool → Switch, array → multi-input, object → nested form)
- Renders appropriate MUI component
- Synchronizes with backend JSON structure

**Why:** Single source of truth (backend JSON), reduces frontend code duplication.

### 6. Scheduled Task Execution

**Problem:** Tasks must run at specific times daily, handle missed runs.

**Solution:** `schedule` library with last run tracking.

**Features:**

- Configurable schedule times (`output/settings.json`)
- Missed run detection on startup
- Next run calculation for UI display

**Implementation:**

```python
for time_str in schedule_times:
    schedule.every().day.at(time_str).do(task)
```

### 7. Data Persistence

**Pattern:** `Serializable` base class with `.save()` and `.load()` methods.

**Features:**

- Automatic JSON serialization
- Directory creation
- Data rotation (missions: 5 days, redemptions: 30 days)

**Why:** Consistent persistence API across all data types.

## Frontend State Management

### Server State (TanStack Query)

- **Use for:** API data (shopping, settings, account, missions)
- **Features:** Caching, automatic refetching, optimistic updates
- **Location:** `services/DataLoader.jsx`

### UI State (React useState/useReducer)

- **Use for:** Form inputs, modal visibility, UI toggles
- **Features:** Local component state, no persistence
- **Location:** Component files, custom hooks

### Form State (Custom hooks)

- **Use for:** Form field synchronization with backend
- **Hooks:** `useFormState`, `useShoppingState`
- **Pattern:** Controlled components with validation

## Browser Automation Workflow

```
User triggers task → Bot.py scheduler
    ↓
Handler.run() (business logic)
    ↓
Automation modules (ImageProcessor, RetryHelper)
    ↓
BrowserService (Playwright interaction)
    ↓
Web page interaction
    ↓
Save results → Send notification
```

**Error Handling:** Graceful degradation with logging at each layer, never crash on element not found.

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

## Build and Packaging

### Development

- Backend: Direct Python execution (`python backend/Bot.py`)
- Frontend: Vite dev server with HMR (`bun run dev`)
- Hot reload: Backend serves frontend build or proxies to Vite

### Production

- Frontend: Build to `frontend/dist/` via Vite
- Backend: PyInstaller bundles Python + frontend + Playwright browsers
- Output: Single executable with embedded resources
- Installer: Inno Setup creates Windows installer

**Key files:**

- `product/Bot.spec`: PyInstaller configuration
- `installer.iss`: Inno Setup script
- `frontend/vite.config.js`: Frontend build config
