---
tags: [glossary]
---

# NSIS

> Nullsoft Scriptable Install System — the open-source Windows installer toolchain Tauri uses to package ZZZ Bot.

## How it works
NSIS compiles a script describing files to copy, registry keys to write, shortcuts to create, and uninstaller entries to register, producing a single `setup.exe`. `cargo tauri build` configures NSIS automatically based on `tauri.conf.json`; ZZZ Bot ships in `src-tauri/target/release/bundle/nsis/`. The installer creates the `output/` directory next to the program so user data ([[Output Files]]) lives outside the install dir and survives upgrades.

## See also
- [[_index]]
- [[NSIS Installer Build]]
- [[NSIS Installer Config]]
