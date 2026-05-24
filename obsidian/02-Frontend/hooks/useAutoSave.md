---
tags: [frontend, hooks]
---

# useAutoSave

> Debounced auto-save wrapper around `useSaveData` exposing a UI-friendly
> status string and a retry callback. Replaces the explicit save-button flow.

## Source
- `frontend/src/hooks/useAutoSave.js` — primary

## How it works
1. Calls `useSaveData(route)` from [[DataLoader]] and keeps the latest
   `mutate` in a ref so the returned `commit` function has stable identity.
2. `commit(value)` stashes the payload and schedules a save after
   `COMMIT_DEBOUNCE_MS` (300ms). Rapid back-to-back calls — drag-then-priority
   edit, multiple Hunt toggles — collapse into a single network round-trip.
3. On success, increments a `savedTick` that flips `showSaved` true for
   `SAVED_PILL_DURATION_MS` (2000ms), then back to false.
4. On unmount, any pending debounced payload is flushed synchronously so a
   user who toggles a switch and immediately tabs away doesn't lose the edit.
5. Derives the `status` string by precedence: `isPending → "saving"`,
   `isError → "error"`, `showSaved → "saved"`, else `"idle"`.
6. `retry()` replays the last attempted payload through `mutate`.

## Returns
- `commit(value)` — schedule a debounced save
- `retry()` — re-attempt the last payload (used by the failure pill)
- `status` — `"idle" | "saving" | "saved" | "error"`
- `error` — the most recent mutation error, if any

## Depends on
- [[DataLoader]] — `useSaveData` mutation and global pending tracking

## Used by
- [[useFormState]] — forms that go through [[ValueAdapter]]
- [[Shopping Page]] — auto-saves selected items + hunt list
- [[Redeem Page]] — auto-saves the rows array on DONE clicks

## Gotchas
- The mutation object returned by `useSaveData` is a new reference every
  render, so the *object* returned by `useAutoSave` also is. Destructure
  `commit` and depend on that — not the whole object — when used inside a
  `useEffect` watcher, or the effect will re-run every render.

## See also
- [[_index]]
- [[SaveStatus]]
- [[Frontend Data Flow]]
