import { useCallback } from "react";
import { useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { DataLoader } from "../services";
import { useAutoSave } from "./useAutoSave";

const HUNT_GATE_SETTING_KEYS = new Set(["run_task", "enable_hunt_mode"]);

function buildOptimisticHuntGate(previousHuntInfo, settings) {
  const enabled = settings.run_task !== false && settings.enable_hunt_mode === true;

  if (!previousHuntInfo && enabled) {
    return previousHuntInfo;
  }

  return {
    ...(previousHuntInfo || {}),
    enabled,
    hunt_items: previousHuntInfo?.hunt_items || [],
    next_hunt_time: enabled ? previousHuntInfo?.next_hunt_time || null : null,
  };
}

/**
 * useFormState Hook
 *
 * Manages form state for route-based data editing with auto-save.
 * Field edits write to the TanStack cache immediately via handleChange and
 * commit() flushes the latest cache snapshot to the backend through
 * useAutoSave. There is no submit button; discrete controls (switch, select,
 * array) commit on change and text fields commit on blur.
 *
 * @returns {Object} Form state and handlers
 *   - value: Current form data (from TanStack cache)
 *   - error: Fetch error if any
 *   - handleChange: Update a single field (optimistic cache write)
 *   - commit: Persist the latest cache value via auto-save
 *   - autoSave: Auto-save status object ({ status, error, retry })
 *   - route: Current route name
 */
export function useFormState(routeOverride) {
  const location = useLocation();
  const route = routeOverride || location.pathname.replace("/", "");
  const queryClient = useQueryClient();

  const { useRouteData } = DataLoader();
  const { data: value = {}, error } = useRouteData(route);
  const autoSave = useAutoSave(route);

  const handleChange = (key, newValue) => {
    const currentValue = queryClient.getQueryData([route]) || value || {};
    const nextValue = {
      ...currentValue,
      [key]: newValue,
    };

    queryClient.setQueryData([route], nextValue);

    if (route === "settings" && HUNT_GATE_SETTING_KEYS.has(key)) {
      queryClient.setQueryData(["overview/hunt"], (previousHuntInfo) =>
        buildOptimisticHuntGate(previousHuntInfo, nextValue),
      );
    }
  };

  const autoSaveCommit = autoSave.commit;
  const commit = useCallback(() => {
    const latest = queryClient.getQueryData([route]);
    if (latest === undefined) return;
    autoSaveCommit(latest);
  }, [autoSaveCommit, queryClient, route]);

  return {
    value,
    error,
    handleChange,
    commit,
    autoSave,
    route,
  };
}
