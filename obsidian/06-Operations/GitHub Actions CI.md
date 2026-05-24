---
tags: [operations]
---

# GitHub Actions CI

> The `.github/` automation layer — CI tests + lint on every push/PR, weekly Dependabot
> update PRs, CodeQL security scanning, and release-please-driven installer releases.

## Source
- `.github/workflows/ci.yml`
- `.github/workflows/codeql.yml`
- `.github/workflows/release.yml`
- `.github/dependabot.yml`
- `release-please-config.json`, `.release-please-manifest.json`

## How it works

**`ci.yml`** — runs on push/PR to `main` and `dev`. Four parallel jobs:

- `backend-tests` on **`windows-latest`** — `uv sync --group dev` → `uv run --group dev
  pytest backend/test/`. Windows because the app only ships for Windows
  ([[NSIS Installer Build]], `winotify`); tests use mocked Playwright objects, so no
  browser install is needed.
- `frontend-build` on **`ubuntu-latest`** — `bun install --frozen-lockfile` → `bun run
  build`. The Vite build is OS-agnostic and needs no env vars.
- `backend-lint` on **`ubuntu-latest`** — `astral-sh/ruff-action@v4.0.0` runs `ruff check
  backend/` then `ruff format --check backend/`. The action downloads the Ruff binary
  standalone — **no Python venv is created** (Ruff doesn't need project deps to lint).
  Config lives in `pyproject.toml` `[tool.ruff]` (line-length 100, import sorting;
  star-import re-exports and `sys.path` shims are excused via per-file-ignores).
- `frontend-lint` on **`ubuntu-latest`** — `bun run lint` (ESLint) + `bun run format:check`
  (Prettier). Config in `frontend/eslint.config.js` and `frontend/.prettierrc.json`.

A `concurrency` group cancels superseded runs on the same ref.

**`codeql.yml`** — CodeQL static analysis for `python` and `javascript-typescript`, on
push/PR to `main`/`dev` plus a weekly cron. Both languages are interpreted, so CodeQL
extracts directly with no build step. The Rust shell in `src-tauri/` is excluded (its
CodeQL support needs a full `cargo build` for marginal value on a thin wrapper).

**`dependabot.yml`** — weekly update PRs for four ecosystems: `uv` (backend), `bun`
(`frontend/`), `cargo` (`src-tauri/`), and `github-actions` (the workflows themselves).
Minor/patch bumps are grouped into one PR per ecosystem; majors stay as individual PRs.

**`release.yml`** — runs on push to `dev`, two jobs:

- `release-please` — `googleapis/release-please-action` maintains a "Release PR" that bumps
  the version in `tauri.conf.json`, `Cargo.toml`, and `pyproject.toml` and updates a root
  `CHANGELOG.md` from Conventional Commits.
- `build` — runs only when merging the Release PR cuts a release. On `windows-latest` it
  installs Playwright Firefox, builds the frontend and the PyInstaller sidecar, builds the
  NSIS installer ([[Production Build Pipeline]]), and `tauri-apps/tauri-action` attaches
  the `.exe` to the GitHub Release.

## Gotchas
- The **default branch is `dev`**, not `main`. Dependabot reads its config, CodeQL sets its
  scanning baseline, and release-please tracks releases — all from the default branch.
- CodeQL needs a public repo or GitHub Advanced Security. The repo is public, so it works.
- ESLint is pinned to v9 — `eslint-plugin-react` is not yet compatible with ESLint 10. Only
  the classic `react-hooks` rules are enabled; the v7 React-Compiler rules are left off.
- Cutting a release requires Conventional Commit messages (`feat:` / `fix:` …) on `dev`.
- **`astral-sh/*` actions ship immutable-only** since `setup-uv@v8.0.0` (2026-03) and
  `ruff-action@v4.0.0` (2026-04) — bare major tags like `@v8` / `@v4` no longer resolve
  and CI fails at "Set up job". Pin to a full version (`@v8.1.0`, `@v4.0.0`) or git SHA;
  Dependabot's `actions-all` group will bump these forward weekly.

## Depends on
- [[uv]]
- [[Test Suite]]
- [[Production Build Pipeline]]

## See also
- [[_index]]
- [[Port Configuration]]
