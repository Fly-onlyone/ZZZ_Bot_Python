# ZZZ Bot — Obsidian Knowledge Vault

This folder is an Obsidian vault. It documents the ZZZ Bot codebase as a graph of
atomic, wikilinked concept notes — designed for fast navigation and discovery rather
than top-down prose.

## How to open

**With Obsidian (recommended):**
1. Install [Obsidian](https://obsidian.md).
2. *Open folder as vault* → select this `obsidian/` folder.
3. Start at [[_HOME]] and follow the reading paths.

**Without Obsidian:**
- Browse the markdown directly on GitHub / your editor. Wikilinks like
  `[[ImageProcessor]]` won't resolve to clickable links, but the file names match the
  wikilink targets — open `01-Backend/automation/ImageProcessor.md` directly.

## Structure

- `_HOME.md` — root Map of Content with reading paths
- `_Templates/` — drop-in templates for new notes
- `00-Architecture/` — cross-cutting flows with Mermaid diagrams
- `01-Backend/` — Python FastAPI + Playwright + OpenCV
- `02-Frontend/` — React 18 + MUI v6 + TanStack Query
- `03-Desktop/` — Tauri Rust shell + PyInstaller sidecar + NSIS installer
- `04-Integrations/` — external systems and runtime libraries (HoYoLab, SQLite, Sentry, etc.)
- `05-Patterns/` — codebase conventions
- `06-Operations/` — build / dev / release / debug
- `07-Glossary/` — domain terms

## When you change the code

The vault travels with the codebase. If you add a new class, flow, or pattern, add or
update the corresponding note. Every leaf folder has an `_index.md` Map of Content —
add your new note to the relevant `_index.md` so it's discoverable.

## Optional CLI smoke test

If you have Obsidian 1.12+ with the CLI enabled (Settings → General → "Enable
Command line interface") and the app running, the official `Obsidian.com` binary can
report graph stats. See `obsidian-init` skill `references/verification.md` for the full
command set.
