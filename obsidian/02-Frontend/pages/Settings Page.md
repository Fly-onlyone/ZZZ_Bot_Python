---
tags: [frontend, pages]
---

# Settings Page

> Three-tab settings editor (General, Tasks, Hunt) driven by ValueAdapter with a Tauri autostart toggle.

## How it works
`TAB_CONFIGS` declares the field list per tab; [[ValueAdapter]] reads each field's type from `settings` and renders a switch/select/text field, with `settingsTypeConfig` overriding `theme`, `hunt_poll_max_wait_seconds`, and `hunt_poll_interval_seconds` to discrete `select` choices. Follows the [[Dynamic Form ValueAdapter Pattern]].

When `run_task === false`, the Tasks and Hunt tabs render an info alert and are dimmed but visible. The General tab also mounts `AutostartToggle` which calls `@tauri-apps/plugin-autostart` `enable`/`disable` and mirrors the result to `/settings.autostart_on_login` (rolls back on persist failure). Tab transitions honour `prefersReducedMotion`.

## Source
- `frontend/src/pages/SettingsPage.jsx` — primary

## Depends on
- [[ValueAdapter]] — form rendering
- [[Settings Endpoints]] — `/settings`
- [[Autostart Reconciliation]] — Tauri plugin

## See also
- [[_index]]
- [[Settings Persistence Flow]]
- [[Settings Contract]]
