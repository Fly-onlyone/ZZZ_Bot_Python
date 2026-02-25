# Code Guide

## Backend Patterns

### Pattern 1: Serializable Data Class

**When to Apply**: Any data that needs persistence.

**Anti-Patterns**:

- Hardcoding file paths (use `resource_path()`)
- Skipping `outside=True` for user data in `output/`
- Not handling missing file case

---

### Pattern 2: Handler with run() Method

**When to Apply**: Task-specific automation workflows.

**Key Points**:

- Standalone handler class with `run()` method
- Return result dict for notifications
- Graceful degradation with logging

---

### Pattern 3: Image Comparison for State Detection

**When to Apply**: Detecting UI states that change dynamically.

**Anti-Patterns**:

- Using relative paths with OpenCV (use `resource_path()`)
- Not logging comparison percentages
- Using fixed selectors for dynamic content

---

### Pattern 4: Retry with Polling

**When to Apply**: Waiting for dynamic elements or state changes.

**Pattern**: Poll with `time.time()` loop; log state transitions; default timeout 180s.

---

### Pattern 5: Three-Phase Hunt Execution

**When to Apply**: Operations that must all succeed before side effects.

Phase 1: Exchange all items (collect codes) → Phase 2: Bulk redeem all codes → Phase 3: Remove successful items from hunt list.

---

### Pattern 6: Centralized Selectors

**When to Apply**: Web automation with CSS selectors.

**Anti-Patterns**:

- Hardcoding selectors in handlers
- Duplicating selectors across files

All selectors live in `backend/automation/Selectors.py`.

---

## Frontend Patterns

### Pattern 7: Dynamic Form with ValueAdapter

**When to Apply**: Rendering forms from JSON data structures.

**How it works**:

- Detects type (bool → Switch, array → multi-input, object → nested form)
- Renders appropriate MUI component
- Synchronizes with backend JSON structure

---

## Animation Guidelines

- Use MUI `component` prop: `<Paper component={motion.div}>`, `<Button component={motion.button}>`
- Do NOT wrap MUI components with `motion()` — use `component=` prop exclusively
- Use staggered `containerVariants`/`itemVariants` for list animations (see `content/` components)
- Prefer transform properties (`scale`, `x`, `y`) over `width`/`height`
- Use `AnimatePresence` with `mode="wait"` for conditional rendering
