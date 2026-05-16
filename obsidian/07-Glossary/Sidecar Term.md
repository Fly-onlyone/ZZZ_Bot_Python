---
tags: [glossary]
---

# Sidecar

> Tauri's name for an external executable bundled with the app and managed as a child process by the Rust shell.

## How it works
In ZZZ Bot the sidecar is the PyInstaller-packaged Python backend (`zzz-bot-<target-triple>.exe`). The Tauri shell spawns it on startup, forwards a [[Desktop Token]] for authentication, and terminates it on quit via [[Sidecar Shutdown Escalation]]. Sidecar binaries live in `src-tauri/binaries/` and are referenced from `tauri.conf.json` under `bundle.externalBin`; the [[Target Triple Term]] suffix is how Tauri resolves the right binary at runtime.

## See also
- [[_index]]
- [[Sidecar Spawn]]
- [[Sidecar Build]]
