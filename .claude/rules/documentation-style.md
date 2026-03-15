# Documentation Style Guide

## Core Principles

1. **Document WHY, not WHAT** - Code shows what, comments explain why
2. **Keep it current** - Outdated docs are worse than none
3. **Be concise** - Every word should add value
4. **Use examples** - Show, don't just tell
5. **Write for future you** - You won't remember in 6 months

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
# outside_path=True: User data that persists across updates
path = resource_path("output/data.json", outside_path=True)
```
