---
tags: [pattern]
---

# Resource Path Resolution Pattern

> `resource_path(rel, outside_path=...)` returns the right absolute path in dev and exe — and decides whether the file lives inside or beside the PyInstaller bundle.

## When to apply
Every file read or write — references in `sample/`, templates in `message/`, user data in `output/`, screenshots, logs.

## The pattern
```python
# Bundled asset (ships inside the exe, read-only)
ref = resource_path("sample/button_exchange.png")

# User data (must persist across exe upgrades)
settings = resource_path("output/settings.json", outside_path=True)
```

`outside_path=True` resolves next to the `.exe` (or project root in dev) so the file survives a PyInstaller `_MEI*` temp wipe.

## Why
Dev runs from the repo root; the packaged exe runs from `sys._MEIPASS`. A naive `"./output/settings.json"` either crashes in exe mode or writes into the temp dir and loses everything on next launch. Centralising the rule avoids both.

## Don't
- Don't omit `outside_path=True` for files in `output/` — they will vanish on the next exe start.
- Don't use `outside_path=True` for bundled samples — they ship inside the exe.
- Don't roll your own path resolution; one helper, one rule.

## See also
- [[_index]]
- [[Serializable Data Pattern]]
- [[SIMULATE_EXE Switch]]
- [[Output Files]]
