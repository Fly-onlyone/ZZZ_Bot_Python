# Documentation Style Guide

## Core Principles

1. **Document WHY, not WHAT** - Code shows what, comments explain why
2. **Keep it current** - Outdated docs are worse than none
3. **Be concise** - Every word should add value
4. **Use examples** - Show, don't just tell
5. **Write for future you** - You won't remember in 6 months

## Python Documentation

### Functions/Methods

```python
def function_name(param: str, optional: int = 10) -> bool:
    """
    Brief description of what it does.

    Args:
        param: Description of parameter
        optional: Description with default behavior

    Returns:
        Description of return value

    Raises:
        ValueError: When this error occurs

    Example:
        result = function_name("value")
    """
```

### Classes

```python
class ClassName:
    """
    Brief description of the class purpose.

    Handles [responsibility]. Used by [consumers].

    Attributes:
        attr_name: Description of attribute

    Example:
        instance = ClassName()
        instance.method()
    """
```

### Complex Logic

```python
# WHY: Explain business rule or non-obvious decision
# Example: Skip validation for admin users per security policy
```

## React/JavaScript Documentation

### Components

```jsx
/**
 * Brief description of component purpose.
 *
 * @param {Object} props - Component props
 * @param {string} props.title - Title to display
 * @param {function} props.onSubmit - Callback when form submits
 * @returns {JSX.Element} Rendered component
 *
 * @example
 * <ComponentName title="Hello" onSubmit={handleSubmit} />
 */
```

### Custom Hooks

```jsx
/**
 * Brief description of what the hook does.
 *
 * @param {Object} initialState - Initial state configuration
 * @returns {Object} { state, handlers }
 *
 * @example
 * const { data, updateData } = useCustomHook(initialData);
 */
```

## Skip Documentation For

- Getters/setters with obvious purpose
- Standard constructors
- Self-documenting code (`get_user_by_id(user_id)`)
- Test files (test names are documentation)
- Handler `run()` methods (behavior documented in CLAUDE.md)

## Section Comments

Use for logical groupings:

```python
# ============================================================
# Section Name
# ============================================================
```

## Words to Avoid

| Avoid | Use Instead |
|-------|-------------|
| "This function..." | Start with verb |
| "Basically" | Remove |
| "Simply" | Remove |
| "Obviously" | Remove |
| "etc." | Be specific |

## Project-Specific Guidelines

### Handler Documentation

- Document non-obvious workflow steps in handler methods
- Log comparison percentages for image matching decisions
- Explain retry logic and timeout values

### Image Comparison Comments

```python
# Compare against "sample/button_exchange.png"
# Threshold: <5% difference indicates Exchange state
diff = compare_images(screenshot, reference)
```

### Path Resolution

```python
# resource_path() handles dev vs exe mode automatically
# outside=True: User data that persists across updates
path = resource_path("output/data.json", outside=True)
```
