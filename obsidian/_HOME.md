---
tags: [moc, home]
---

# ZZZ Bot — Knowledge Vault

A graph-linked tour of the ZZZ Bot codebase. **Start with the architecture flows** to
build mental scaffolding, then drill into modules or patterns as needed.

> **ZZZ Bot** is a Windows desktop automation tool for *Zenless Zone Zero* (HoYoverse).
> It runs scheduled Playwright + OpenCV automation against the HoYoLab event website
> (daily check-ins, shopping, redemptions, hunt mode), exposes a FastAPI backend, and
> ships as a Tauri-bundled NSIS installer that wraps a PyInstaller-built Python sidecar
> and a React 18 + MUI v6 + TanStack Query UI.

## 🧭 Start here — Architecture flows

- [[Daily Task Cycle]] — top-level scheduler → handlers → email
- [[Browser Session Lifecycle]] — persistent Playwright context
- [[Hunt Mode Lifecycle]] — three-phase timed item purchase
- [[Image Recognition Pipeline]] — OpenCV template matching for UI state
- [[Locator Telemetry Pipeline]] — selector tracking → SQLite → frontend
- [[Manual Login Flow]] — SessionState machine for browser handoff
- [[Notification Pipeline]] — Jinja2 → SMTP/Apprise → frontend SSE
- [[Settings Persistence Flow]] — SQLite + settings.json mirror
- [[Sidecar Lifecycle]] — Tauri spawn → ready → graceful shutdown
- [[Frontend Data Flow]] — TanStack Query + DataLoader + SSE updates

## 🐍 Backend (Python)

→ [[01-Backend/_index|All backend modules]]

- [[01-Backend/core/_index|core]] — entry point, globals, notifications, manual login
- [[01-Backend/handlers/_index|handlers]] — Mission, Shopping, Draw, Hunt
- [[01-Backend/automation/_index|automation]] — Playwright + OpenCV + locator tracking
- [[01-Backend/services/_index|services]] — browser session manager
- [[01-Backend/repositories/_index|repositories]] — embedded SQLite + legacy JSON
- [[01-Backend/domain/_index|domain]] — typed models and enums
- [[01-Backend/api/_index|api]] — 35+ FastAPI endpoints
- [[01-Backend/utils/_index|utils]] — data, notifications, logging, screenshots
- [[01-Backend/strategies/_index|strategies]] — image comparison strategy
- [[01-Backend/message/_index|message]] — Jinja2 email templates

## ⚛️ Frontend (React)

→ [[02-Frontend/_index|All frontend modules]]

- [[02-Frontend/pages/_index|pages]] — Overview, Shopping, Settings, Account, Tools…
- [[02-Frontend/content/_index|content]] — reusable page sections
- [[02-Frontend/components/_index|components]] — common, fields, layout, forms
- [[02-Frontend/hooks/_index|hooks]] — form state, SSE, drag-drop, zoom
- [[02-Frontend/services/_index|services]] — DataLoader (TanStack Query) + Sentry
- [[02-Frontend/theme/_index|theme]] — 4-theme system (Nebula/Venom/Glacier/Cyber)
- [[02-Frontend/config/_index|config]] — constants, stale times
- [[02-Frontend/routes/_index|routes]] — PermanentDrawer router
- [[02-Frontend/entry/_index|entry]] — main.jsx, global CSS

## 🖥️ Desktop shell

→ [[03-Desktop/_index|All desktop concepts]]

Tray menu, sidecar lifecycle, window state dual storage, autostart reconciliation,
PyInstaller-to-Tauri bridging, NSIS installer.

## 🔌 External integrations

→ [[04-Integrations/_index|All integrations]]

## 🧩 Patterns

→ [[05-Patterns/_index|All patterns]]

## 🛠️ Operations

→ [[06-Operations/_index|All operations]]

## 📖 Glossary

→ [[07-Glossary/_index|Glossary]]

## 🎯 Reading paths

**New contributor:**
[[Daily Task Cycle]] → [[Bot Entry Point]] → [[MissionHandler]] → [[ImageProcessor]] → [[Selectors]] → [[Image Comparison State Detection Pattern]]

**Frontend developer:**
[[Frontend Data Flow]] → [[Frontend Entry Point]] → [[PermanentDrawer Router]] → [[ValueAdapter]] → [[Dynamic Form ValueAdapter Pattern]] → [[ThemeContext]]

**DevOps / packaging:**
[[Sidecar Lifecycle]] → [[Sidecar Spawn]] → [[Sidecar Shutdown Escalation]] → [[PyInstaller Sidecar Build]] → [[Prepare Tauri Sidecar Script]] → [[NSIS Installer Build]] → [[Port Configuration]] → [[GitHub Actions CI]]

**Hunt-mode developer:**
[[Hunt Mode Lifecycle]] → [[HuntModeHandler]] → [[Three-Phase Hunt Execution Pattern]] → [[ShoppingHandler]] → [[RedeemAutofill]] → [[StringUtil]]

**Locator-tracker debugger:**
[[Locator Telemetry Pipeline]] → [[LocatorTracker]] → [[Tracking Helpers]] → [[Screenshot Store]] → [[Locator Tracker Page]] → [[Locator Tracker Instrumentation Pattern]]
