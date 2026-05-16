---
tags: [desktop]
---

# Tauri Shell Entry

> Rust desktop shell entry point that delegates to the library crate where the full app lifecycle lives.

## Source
- `src-tauri/src/main.rs` — primary (6-line binary stub)
- `src-tauri/src/lib.rs` — `run()` builder, plugin registration, setup hooks

## How it works
`main.rs` only suppresses the Windows console (release builds) and calls `zzz_bot_lib::run()`. The library crate builds the `tauri::Builder`, registers the `shell`, `autostart`, and `log` plugins, manages `AppRuntime` / `WindowStateCache` state, spawns the backend sidecar, builds the tray, reconciles autostart and startup window visibility, and wires window-event + run-event handlers (geometry caching, debounced persistence, graceful shutdown on `ExitRequested` / `Exit`).

## Depends on
- [[Tauri]] — Rust shell framework (`2.10.0`, tray-icon feature)
- [[Sidecar Spawn]] — backend lifecycle started during `setup`
- [[Tray Menu]] — tray built during `setup`
- [[Autostart Reconciliation]] — kicked off in `setup`

## Used by
- [[Sidecar Lifecycle]] — owns the sidecar process across the app run
- [[Window State Dual Storage]] — wires window events to persistence

## See also
- [[_index]]
- [[Backend Port Resolution]]
