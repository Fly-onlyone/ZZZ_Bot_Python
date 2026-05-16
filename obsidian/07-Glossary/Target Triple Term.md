---
tags: [glossary]
---

# Target Triple

> Rust's compile-target identifier in the form `arch-vendor-os-env`, e.g. `x86_64-pc-windows-msvc`.

## How it works
The triple tells the Rust toolchain (and Tauri's resolver) which platform a binary is for. Tauri's sidecar mechanism appends the triple to the binary filename so it can pick the right one at runtime — for ZZZ Bot the [[PyInstaller Term]]-built sidecar is renamed `zzz-bot-<target-triple>.exe` (typically `zzz-bot-x86_64-pc-windows-msvc.exe`) before being dropped into `src-tauri/binaries/`. A mismatched triple makes Tauri fail to locate the sidecar at startup.

## See also
- [[_index]]
- [[Sidecar Build]]
- [[Prepare Tauri Sidecar Script]]
