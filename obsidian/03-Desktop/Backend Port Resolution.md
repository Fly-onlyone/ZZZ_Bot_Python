---
tags: [desktop]
---

# Backend Port Resolution

> Tauri shell picks the backend port from the `ZZZ_DEV_BACKEND_PORT` env var, falling back to `8000` for production builds — and, in release, to a free port if `8000` is taken.

## Source
- `src-tauri/src/lib.rs` — `backend_port()`, `port_is_available()`, `allocate_free_port()`, `resolve_backend_port()`

## How it works
`backend_port()` is the *preferred* port:
```rust
std::env::var("ZZZ_DEV_BACKEND_PORT")
    .ok()
    .and_then(|v| v.parse::<u16>().ok())
    .filter(|port| *port > 0)
    .unwrap_or(8000)
```

`setup()` resolves the actual port **once**, then stores it in `AppRuntime.backend_port`:
```rust
let port = if cfg!(debug_assertions) { backend_port() } else { resolve_backend_port() };
```
- **Debug** (`cargo tauri dev`): use `backend_port()` as-is — the dev runner (`run-tauri-app.ts`) already fixed the port and started the backend, so Rust must not diverge.
- **Release:** `resolve_backend_port()` returns the preferred port if `TcpListener::bind` succeeds, else an OS-allocated free port (mirrors the dev fallback in [[Bot Entry Point]]).

The resolved port is used in **three** places, all reading the single stored value so they can never disagree:

1. **`backend_url`** (`http://127.0.0.1:{port}`) stored in `AppRuntime` — every HTTP call (settings, shutdown, run-playwright) targets this.
2. **`--port` arg** passed to the sidecar process when spawning (reads `runtime.backend_port`).
3. **`window.__ZZZ_BACKEND_URL__`** injected into the WebView via the main window's `initialization_script` (the window is now built in Rust, not `tauri.conf.json`, so it can carry the script). The frontend reads this global first — see [[Frontend Constants]].

Production prefers `8000` to avoid clashing with a dev backend on `8001`. When running `tauri dev` against a manually-started dev backend, set `ZZZ_DEV_BACKEND_PORT=8001`.

## Depends on
- [[Port Configuration]] — project-wide port convention

## Used by
- [[Sidecar Spawn]] — `--port` arg
- [[Tauri Shell Entry]] — `backend_url` for all HTTP calls; builds the main window with the URL-injecting init script
- [[Frontend Constants]] — reads the injected `window.__ZZZ_BACKEND_URL__`

## See also
- [[_index]]
- [[Bot Entry Point]]
