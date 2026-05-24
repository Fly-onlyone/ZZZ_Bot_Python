---
tags: [architecture, flow]
---

# Settings Persistence Flow

> Settings live in the embedded SQLite database (one row in the `documents` table,
> `collection='settings'`) and are also surfaced as `output/settings.json` for legacy
> compatibility and easy human inspection. The frontend reads via `/settings`; the
> Tauri shell also reads a subset directly to bootstrap window state before the
> backend is ready.

## Source

- `backend/repositories/DataStore.py` — `_SINGLE_DOC_COLLECTIONS` includes settings/account/shopping
- `backend/api/routes.py` — `/settings`, `/settings/advanced`
- `frontend/src/services/DataLoader.jsx` — query/mutation per route
- `output/settings.json` — legacy/inspection mirror

## How it works

```mermaid
sequenceDiagram
    participant FE as Frontend (SettingsPage)
    participant AS as useAutoSave
    participant API as FastAPI
    participant DS as DataStore
    participant FS as output/settings.json

    FE->>API: GET /settings
    API->>DS: get_settings() — documents row, collection='settings'
    DS-->>API: payload
    API-->>FE: payload
    FE->>FE: user edits a field
    Note over FE: switch/select/array → commit on change<br/>text input → commit on blur
    FE->>AS: commit(latest cache value)
    AS->>AS: debounce 300ms
    AS->>API: POST /settings
    API->>DS: save_settings() — upsert documents row
    DS->>FS: also writes legacy JSON mirror
    DS-->>API: ok
    API-->>AS: 200
    AS-->>FE: status "saved" (SaveStatus pill)
```

The frontend has no submit button — [[useAutoSave]] fires the mutation
automatically when the user blurs a text field or flips a switch/select/array
control. The legacy JSON mirror lets the Tauri shell read `output/settings.json`
directly to recover `autostart_on_login` and window geometry without waiting
for the sidecar to start. SQLite is an embedded file, so there is no connection
to lose and no runtime-reconnect step — a settings save never has to reconcile
a database URI.

## Depends on

- [[DataStore]] — primary store
- [[Settings Endpoints]] — REST layer
- [[DataLoader]] — frontend cache
- [[useAutoSave]] — debounced commit + status
- [[Settings Page]] — UI
- [[ValueAdapter]] — dynamic form

## Used by

- [[Daily Task Cycle]] — reads `schedule_times`, `hide_browser`, `exit_after_run`
- [[Tauri Shell Entry]] — reads `autostart_on_login`, window geometry
- [[ThemeContext]] — reads persisted `theme` on mount

## Gotchas

- Two writers: the SQLite `documents` table and the Tauri shell's local `window-state.json`. See [[Window State Dual Storage]] for the merge rule.
- Adding a new persisted field also requires updating [[Settings Contract]] if it's an "advanced" setting.

## See also

- [[_index]]
- [[DataStore]]
- [[Settings Endpoints]]
- [[Window State Dual Storage]]
