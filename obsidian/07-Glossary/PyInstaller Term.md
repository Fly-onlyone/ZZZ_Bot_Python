---
tags: [glossary]
---

# PyInstaller

> A Python-to-standalone-executable bundler that packs the interpreter, source, and dependencies into a single `.exe`.

## How it works
At build time PyInstaller follows imports from an entry script, collects every module and data file, and embeds them alongside a CPython runtime. At launch the exe extracts itself to a temp folder (`sys._MEIPASS`) and runs. ZZZ Bot uses PyInstaller to produce the Tauri [[Sidecar Term]]; because the runtime path differs from dev, every file access has to go through [[Resource Path Resolution Pattern]] so dev and exe behave the same.

## See also
- [[_index]]
- [[Sidecar Build]]
- [[PyInstaller]]
