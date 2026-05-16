---
tags: [frontend, services]
---

# Sentry Logger

> Thin wrappers around `Sentry.logger` that normalize attributes and short-circuit when Sentry is disabled.

## Source
- `frontend/src/services/sentryLogger.js` — primary

## How it works
Exports three functions — `logInfo(msg, attrs)`, `logWarn(msg, attrs)`, `logError(msg, error, attrs)`. Each:

1. Returns early when `Sentry.isEnabled()` is false (Sentry not initialized or sampled out).
2. Normalizes the attribute bag via `normalizeAttributes`: passes through primitives, formats `Error` as `"Name: message"`, stringifies objects via `JSON.stringify` (falls back to `String()`), maps `null` to `"null"`, drops `undefined`.
3. `logError` additionally injects `errorName`/`errorMessage` into attributes and, when the value is an `Error` instance, calls `Sentry.captureException(error, { level: "error", extra })` for full stack traces.

## Depends on
- [[Sentry]] — `@sentry/react` SDK + structured `logger` API

## Used by
- [[DataLoader]], [[useFormState]], [[useTaskEvents]], [[PermanentDrawer Router]] — all frontend telemetry flows through here

## Gotchas
- Plain strings or objects passed to `logError` won't produce stack traces — only `Error` instances trigger `captureException`.

## See also
- [[_index]]
- [[DataLoader]]
