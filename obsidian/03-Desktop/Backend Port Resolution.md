---
tags: [desktop]
---

# Backend Port Resolution

> Tauri shell picks the backend port from the `ZZZ_DEV_BACKEND_PORT` env var, falling back to `8000` for production builds.

## Source
- `src-tauri/src/lib.rs` — `backend_port()`

## How it works
```rust
std::env::var("ZZZ_DEV_BACKEND_PORT")
    .ok()
    .and_then(|v| v.parse::<u16>().ok())
    .filter(|port| *port > 0)
    .unwrap_or(8000)
```

The resolved port is used in two places:

1. **`backend_url`** (`http://127.0.0.1:{port}`) stored in `AppRuntime` — every HTTP call (settings, shutdown, run-playwright) targets this.
2. **`--port` arg** passed to the sidecar process when spawning.

Production uses `8000` by default to avoid clashing with a dev backend on `8001`. When running `tauri dev` against a manually-started dev backend, set `ZZZ_DEV_BACKEND_PORT=8001`.

## Depends on
- [[Port Configuration]] — project-wide port convention

## Used by
- [[Sidecar Spawn]] — `--port` arg
- [[Tauri Shell Entry]] — `backend_url` for all HTTP calls

## See also
- [[_index]]
- [[Bot Entry Point]]
