---
tags: [integration]
---

# Bun

> JavaScript runtime + package manager for the frontend; replaces npm/yarn and runs the sidecar prep TypeScript script directly.

## Used for
- Installing frontend deps: `bun install`
- Running Vite: `bun run dev` / `bun run build`
- Executing TypeScript scripts directly: `bun run tauri:prepare-sidecar`
- `bun run check:hook-order` — React hook order lint pre-build

## Configuration
- Pinned via `packageManager: "bun@1.3.9"` (`frontend/package.json`)
- `@types/bun ^1.3.10` for the prep script

## Wire-up
- `frontend/package.json` — scripts
- `frontend/scripts/prepare-tauri-sidecar.ts` — bun-run TypeScript

## Auth mode
N/A

## Gotchas
- Don't fall back to `npm` / `yarn` — the lockfile (`bun.lockb`) won't be regenerated correctly and dependency versions may drift.

## See also
- [[_index]]
- [[Prepare Tauri Sidecar Script]]
- [[Vite]]
