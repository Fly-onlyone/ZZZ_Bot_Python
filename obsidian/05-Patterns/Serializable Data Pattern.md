---
tags: [pattern]
---

# Serializable Data Pattern

> Wrap persisted JSON in a data class that knows its own path, load, and save.

## When to apply
Any data that needs to round-trip to disk — settings, credentials, shopping lists, mission reports. If two modules read the same JSON, this pattern is mandatory.

## The pattern
```python
class SettingsData:
    PATH = resource_path("output/settings.json", outside_path=True)

    @classmethod
    def load(cls):
        if not os.path.exists(cls.PATH):
            return cls.default()
        with open(cls.PATH, "r", encoding="utf-8") as f:
            return cls(**json.load(f))

    def save(self):
        os.makedirs(os.path.dirname(self.PATH), exist_ok=True)
        with open(self.PATH, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2)
```

## Why
The path lives next to the schema, so renaming the file is one edit. `outside_path=True` keeps user data outside the PyInstaller temp dir so it survives upgrades.

## Don't
- Don't hardcode relative paths — use `resource_path()` so dev and exe both resolve correctly.
- Don't omit `outside_path=True` for files in `output/` — they'll be wiped on every exe launch.
- Don't assume the file exists — handle the missing-file case explicitly.

## See also
- [[_index]]
- [[Resource Path Resolution Pattern]]
- [[DataRepository]]
- [[Output Files]]
