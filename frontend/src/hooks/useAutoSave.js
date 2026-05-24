import { useCallback, useEffect, useRef, useState } from "react";
import { DataLoader } from "../services";

const COMMIT_DEBOUNCE_MS = 300;
const SAVED_PILL_DURATION_MS = 2000;

/**
 * useAutoSave Hook
 *
 * Wraps DataLoader.useSaveData with a debounced commit() and a UI-friendly
 * status string. Callers invoke commit(value) whenever a user edit lands;
 * rapid calls within COMMIT_DEBOUNCE_MS collapse into one network save.
 *
 * `isPending` is true while a commit is queued in the debounce window OR an
 * in-flight save is on the wire — consumers can use it to gate hydration
 * effects that would otherwise clobber the user's unsaved edit when a refetch
 * lands mid-debounce.
 *
 * @param {string} route - Route name passed through to useSaveData
 * @returns {{
 *   commit: (value: unknown) => void,
 *   retry: () => void,
 *   status: "idle" | "saving" | "saved" | "error",
 *   isPending: boolean,
 *   error: unknown
 * }}
 */
export function useAutoSave(route) {
  const { useSaveData } = DataLoader();
  const mutation = useSaveData(route);

  // mutation.mutate is stable, but the object reference is not — keep a ref so
  // commit() and the unmount-flush effect can call the latest mutate without
  // changing their own identity each render.
  const mutateRef = useRef(mutation.mutate);
  mutateRef.current = mutation.mutate;

  const timeoutRef = useRef(null);
  const pendingPayloadRef = useRef(undefined);
  const lastPayloadRef = useRef(undefined);

  const [savedTick, setSavedTick] = useState(0);
  const [showSaved, setShowSaved] = useState(false);
  const [hasDebouncedCommit, setHasDebouncedCommit] = useState(false);

  const sendNow = useCallback((payload) => {
    lastPayloadRef.current = payload;
    mutateRef.current(payload, {
      onSuccess: () => setSavedTick((tick) => tick + 1),
    });
  }, []);

  const commit = useCallback(
    (value) => {
      pendingPayloadRef.current = value;
      setHasDebouncedCommit(true);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        timeoutRef.current = null;
        const payload = pendingPayloadRef.current;
        pendingPayloadRef.current = undefined;
        setHasDebouncedCommit(false);
        if (payload === undefined) return;
        sendNow(payload);
      }, COMMIT_DEBOUNCE_MS);
    },
    [sendNow],
  );

  const retry = useCallback(() => {
    if (lastPayloadRef.current === undefined) return;
    sendNow(lastPayloadRef.current);
  }, [sendNow]);

  useEffect(() => {
    if (savedTick === 0) return undefined;
    setShowSaved(true);
    const id = setTimeout(() => setShowSaved(false), SAVED_PILL_DURATION_MS);
    return () => clearTimeout(id);
  }, [savedTick]);

  // Flush any debounced edit when the component unmounts so the user's last
  // change isn't dropped if they navigate away within the debounce window.
  useEffect(
    () => () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        const payload = pendingPayloadRef.current;
        pendingPayloadRef.current = undefined;
        if (payload !== undefined) {
          sendNow(payload);
        }
      }
    },
    [sendNow],
  );

  let status = "idle";
  if (mutation.isPending) status = "saving";
  else if (mutation.isError) status = "error";
  else if (showSaved) status = "saved";

  const isPending = hasDebouncedCommit || mutation.isPending;

  return { commit, retry, status, isPending, error: mutation.error };
}
