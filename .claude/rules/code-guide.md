# Code Guide

This file consolidates naming conventions, code patterns, and animation guidelines.

---

## Naming Conventions

### Backend (Python)

| Element           | Convention            | Example                                |
|-------------------|-----------------------|----------------------------------------|
| Modules/Packages  | lowercase_underscores | `image_processor`, `hunt_mode_handler` |
| Classes           | PascalCase            | `MissionHandler`, `ImageProcessor`     |
| Functions/Methods | snake_case            | `run_hunt`, `get_next_hunt_time`       |
| Constants         | UPPER_SNAKE_CASE      | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`   |
| Private members   | Leading underscore    | `_internal_method`, `_cache`           |

### Frontend (React/JavaScript)

| Element    | Convention                  | Example                                  |
|------------|-----------------------------|------------------------------------------|
| Components | PascalCase                  | `Overview`, `ShoppingPage`, `SaveButton` |
| Files      | Match component name        | `Overview.jsx`, `ShoppingPage.jsx`       |
| Hooks      | camelCase with `use` prefix | `useFormState`, `useShoppingState`       |
| Functions  | camelCase                   | `handleSubmit`, `fetchData`              |
| Constants  | UPPER_SNAKE_CASE            | `API_BASE_URL`, `MAX_ITEMS`              |

### File Organization

- **Backend:** Organize by layer (handlers, automation, services, repositories)
- **Frontend:** Organize by type (pages, components, hooks, services)
- **Barrel exports:** Use `index.js` for clean imports
- **Test files:** Mirror source structure in `backend/test/`

---

## Code Style

### Python

- **Import order:** Standard library → Third-party → Local modules
- **Type hints:** Use for function signatures (Pydantic models for data)
- **Docstrings:** For public APIs and complex logic
- **Error handling:** Graceful degradation with logging, avoid crashes
- **Path resolution:** Always use `resource_path()` for cross-mode compatibility

### React/JavaScript

- **Imports:** Named exports over default exports
- **State management:** TanStack Query for server state, React state for UI
- **Styling:** Emotion (CSS-in-JS) with MUI theme system
- **Props:** Destructure in function signature
- **Event handlers:** Prefix with `handle` (`handleClick`, `handleSubmit`)

---

## Backend Patterns

### Pattern 1: Serializable Data Class

**When to Apply**: Any data that needs JSON persistence.

```python
class MyData(Serializable):
    """Data class with automatic JSON persistence."""

    def __init__(self):
        super().__init__()
        self.items = []
        self.metadata = {}

    def save(self):
        """Save to output/{filename}.json"""
        path = resource_path("output/mydata.json", outside=True)
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def load(cls):
        """Load from JSON, create new if not exists."""
        path = resource_path("output/mydata.json", outside=True)
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = cls()
                data.__dict__.update(json.load(f))
                return data
        return cls()
```

**Anti-Patterns**:

- Hardcoding file paths (use `resource_path()`)
- Skipping `outside=True` for user data
- Not handling missing file case

---

### Pattern 2: Handler with run() Method

**When to Apply**: Task-specific automation workflows.

```python
class TaskHandler:
    """Orchestrates a specific automation task."""

    def __init__(self, page: Page):
        self.page = page
        self.image_processor = ImageProcessor()

    async def run(self) -> dict:
        """Execute the task workflow."""
        try:
            await self._navigate_to_target()
            result = await self._execute_actions()
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Task failed: {e}")
            return {"success": False, "error": str(e)}
```

**Key Points**:

- Standalone handler class with `run()` method
- Return result dict for notifications
- Graceful degradation with logging

---

### Pattern 3: Image Comparison for State Detection

**When to Apply**: Detecting UI states that change dynamically.

```python
def check_button_state(screenshot_path: str) -> str:
    """Detect button state via image comparison."""
    screenshot = cv2.imread(screenshot_path)

    references = {
        "exchange": "sample/button_exchange.png",
        "finished": "sample/button_finished.png",
    }

    for state, ref_path in references.items():
        reference = cv2.imread(resource_path(ref_path))
        diff = compare_images(screenshot, reference)
        logger.debug(f"Comparison with {state}: {diff:.2f}%")

        if diff < 5.0:  # <5% difference = match
            return state

    return "unavailable"
```

**Anti-Patterns**:

- Using relative paths with OpenCV
- Not logging comparison percentages
- Using fixed selectors for dynamic content

---

### Pattern 4: Retry with Polling

**When to Apply**: Waiting for dynamic elements or state changes.

```python
async def wait_for_element(
    page: Page,
    check_func: Callable,
    timeout: int = 180,
    interval: float = 1.0
) -> bool:
    """Poll until condition is met or timeout."""
    start = time.time()
    last_state = None

    while time.time() - start < timeout:
        current_state = await check_func()

        if current_state != last_state:
            logger.info(f"State changed: {last_state} -> {current_state}")
            last_state = current_state

        if current_state == "ready":
            return True

        await asyncio.sleep(interval)

    logger.warning(f"Timeout after {timeout}s")
    return False
```

---

### Pattern 5: Three-Phase Hunt Execution

**When to Apply**: Operations that must all succeed before side effects.

```python
async def run_hunt(self, items: list[str]) -> dict:
    """
    Execute hunt in three phases to avoid session timeout.

    Phase 1: Exchange all items (collect codes)
    Phase 2: Redeem all codes
    Phase 3: Update hunt list (remove successful items)
    """
    codes = []

    # Phase 1: Exchange only
    for item in items:
        code = await self.exchange_item_only(item)
        if code:
            codes.append(code)

    # Phase 2: Bulk redeem
    results = await self.redeem_all_codes(codes)

    # Phase 3: Cleanup hunt list
    await self.remove_successful_items(results["success"])

    return {
        "exchanged": len(codes),
        "redeemed": results["success"],
        "failed": results["failed"]
    }
```

---

### Pattern 6: API Route with Pydantic Validation

**When to Apply**: REST API endpoints.

```python
from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter()

class SettingsUpdate(BaseModel):
    schedule_times: list[str]
    hide_browser: bool = True

@router.post("/settings")
async def update_settings(data: SettingsUpdate):
    """Update application settings."""
    settings = Settings.load()
    settings.schedule_times = data.schedule_times
    settings.hide_browser = data.hide_browser
    settings.save()
    return {"status": "ok"}
```

**Anti-Patterns**:

- Accepting raw dict without validation
- Business logic in route handlers (use services)

---

### Pattern 7: Centralized Selectors

**When to Apply**: Web automation with CSS selectors.

```python
# backend/automation/Selectors.py
"""Centralized selector constants for maintainability."""

# ===== MISSION SELECTORS =====
MISSION_DIALOG_CLOSE = ".components-pc-assets-__dialog_---dialog-close---3G9gO2"
MISSION_WRAPPER = ".wrapper-O3T67n"

# ===== SHOPPING SELECTORS =====
SHOPPING_ITEM = ".item-6Owrjq"
SHOPPING_ITEM_BUTTON = ".itemBtn-gTL1Rd"

# Usage in handlers:
from automation.Selectors import SHOPPING_ITEM, SHOPPING_ITEM_BUTTON
```

**Anti-Patterns**:

- Hardcoding selectors in handlers
- Duplicating selectors across files

---

## Frontend Patterns

### Pattern 8: Dynamic Form with ValueAdapter

**When to Apply**: Rendering forms from JSON data structures.

```jsx
<ValueAdapter
  label="Configuration"
  value={configData}
  onChange={handleConfigChange}
  typeConfig={{
    password: (props) => <PasswordField {...props} />,
    schedule_times: (props) => <TimeArrayField {...props} />,
  }}
/>
```

**How it works**:

- Detects type (bool → Switch, array → multi-input, object → nested form)
- Renders appropriate MUI component
- Synchronizes with backend JSON structure

---

### Pattern 9: Content Component

**When to Apply**: Page sections that display specific data.

```jsx
// frontend/src/content/Hunt.jsx
export default function Hunt() {
  const { useRouteData } = DataLoader();
  const { data, error } = useRouteData("overview/hunt");

  if (error) return <Alert severity="error">{error.message}</Alert>;
  if (!data) return <Typography>Loading...</Typography>;

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants}>
      {/* Content */}
    </motion.div>
  );
}
```

**Existing Content Components**:

- `Mission.jsx` - Mission history and reports (`/overview/mission`)
- `Hunt.jsx` - Hunt mode status and items (`/overview/hunt`)
- `RunningStatus.jsx` - Last/next run times (`/check-run-status`)

---

### Pattern 10: ThemeContext Provider

**When to Apply**: Application-wide theme that syncs with backend settings.

```jsx
import { createContext, useContext } from 'react';

const ThemeContext = createContext();

export function useThemeContext() {
  return useContext(ThemeContext);
}

export const ThemeProvider = ({ children }) => {
  const [themeName, setThemeName] = useState('nebula');
  const colors = themes[themeName] || themes.nebula;

  return (
    <ThemeContext.Provider value={{ themeName, themeColors: colors, setThemeName }}>
      {children}
    </ThemeContext.Provider>
  );
};
```

**Available Themes**: `nebula` (default), `venom`, `glacier`, `cyber`

---

### Pattern 11: SectionCard with Framer Motion

**When to Apply**: Reusable card components with animations.

```jsx
import { motion } from 'framer-motion';
import { memo } from 'react';

const MotionCard = motion(Card);

export const SectionCard = memo(({ title, icon: Icon, children }) => {
  const { themeColors } = useThemeContext();

  return (
    <MotionCard
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      sx={{ background: themeColors.cardBg }}
    >
      <CardHeader
        avatar={
          <motion.div whileHover={{ rotate: 5, scale: 1.1 }}>
            <Avatar><Icon /></Avatar>
          </motion.div>
        }
        title={title}
      />
      <CardContent>{children}</CardContent>
    </MotionCard>
  );
});
```

---

## Animation Patterns (MUI + Framer Motion)

### MUI Integration Techniques

**Technique 1: MUI `component` Prop (Recommended)**

```jsx
<Button
  component={motion.button}
  variant="contained"
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
>
  Click Me
</Button>

<Box
  component={motion.div}
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
>
  Content
</Box>
```

| MUI Component           | Motion Type                 |
|-------------------------|-----------------------------|
| Button                  | `motion.button`             |
| Box, Stack, Grid, Paper | `motion.div`                |
| Icon (SVG)              | `motion.svg`                |
| Typography              | `motion.p` or `motion.span` |

**Technique 2: Wrap MUI with motion()**

```jsx
const MotionGrid = motion(Grid);
const MotionCard = motion(Card);
```

---

### Staggered Children

```jsx
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { when: "beforeChildren", staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { type: "spring", bounce: 0.4 } }
};

<motion.div initial="hidden" animate="visible" variants={containerVariants}>
  {items.map((item) => (
    <motion.div key={item.id} variants={itemVariants}>
      <Card>{item.content}</Card>
    </motion.div>
  ))}
</motion.div>
```

---

### Variant Propagation

```jsx
// Parent defines animate prop, children inherit automatically
<motion.div initial="initial" whileHover="hover">
  <motion.div variants={{ initial: { scale: 1 }, hover: { scale: 1.1 } }} />
  <motion.div variants={{ initial: { opacity: 0.5 }, hover: { opacity: 1 } }} />
</motion.div>
```

---

### AnimatePresence (Exit Animations)

```jsx
<AnimatePresence mode="wait">
  {isOpen && (
    <motion.div
      key="modal"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
    >
      <Card>Modal Content</Card>
    </motion.div>
  )}
</AnimatePresence>
```

---

### Layout Animations

```jsx
<motion.div layout>
  {/* CSS changes animate smoothly */}
</motion.div>

<motion.div layoutId="shared-element">
  {/* Element animates between positions */}
</motion.div>
```

---

### Gesture Feedback

```jsx
<motion.div
  whileHover={{ scale: 1.05, boxShadow: "0 10px 30px rgba(0,0,0,0.2)" }}
  whileTap={{ scale: 0.95 }}
  transition={{ type: "spring", stiffness: 400, damping: 17 }}
>
  <Card>Interactive Card</Card>
</motion.div>
```

---

### Transition Reference

| Type   | Use For                              | Example                                               |
|--------|--------------------------------------|-------------------------------------------------------|
| Spring | Buttons, cards, interactive elements | `{ type: "spring", stiffness: 400, damping: 17 }`     |
| Tween  | Modals, fades, progress indicators   | `{ type: "tween", duration: 0.3, ease: "easeInOut" }` |

---

### Performance Best Practices

1. **Memoize animated sub-components** - Prevents unnecessary re-renders
2. **Use `layout` sparingly** - Only on elements that actually change position
3. **Prefer transform properties** - `scale`, `rotate`, `x`, `y` over `width`, `height`
4. **Use variants pattern** - For state-based animations instead of inline objects
5. **Unique keys on list items** - Required for AnimatePresence tracking

---

### Animation Anti-Patterns

| Don't                                                 | Do Instead                        |
|-------------------------------------------------------|-----------------------------------|
| Wrap MUI in `<motion.div>`                            | Use `component={motion.div}` prop |
| Animate width/height directly                         | Use `scale` or `layout`           |
| Heavy animations on frequently re-rendered components | Memoize or use CSS transitions    |
| `initial`/`animate` on list items without `key`       | Always use unique keys            |

---

## When NOT to Use Patterns

- **YAGNI**: Don't add abstractions for hypothetical futures
- **Simple cases**: Direct implementation beats pattern overhead
- **Single use**: Patterns shine with repetition
- **Team unfamiliarity**: Unknown patterns reduce maintainability
