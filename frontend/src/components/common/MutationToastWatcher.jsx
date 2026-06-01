import { useEffect } from "react";
import { useMutationState } from "@tanstack/react-query";

import { MAINTENANCE_TASKS } from "../../config/maintenanceTasks";
import { useNotification } from "./NotificationContext";

// Module-level so the "last shown" marker survives MutationToastWatcher
// unmounts (which shouldn't happen in normal use — but keeps us idempotent
// across HMR reloads and React StrictMode double-mounts).
const _lastShownByRoute = new Map();

function selectMutationState(mutation) {
  return {
    submittedAt: mutation.state.submittedAt,
    status: mutation.state.status,
    data: mutation.state.data,
    error: mutation.state.error,
  };
}

/**
 * App-level subscriber that watches the TanStack MutationCache for completed
 * maintenance mutations and fires the global notification toast — even when
 * the page that started the mutation is no longer mounted.
 *
 * Renders nothing. Mount once inside NotificationProvider.
 */
export default function MutationToastWatcher() {
  const { showAlert } = useNotification();

  // useMutationState is a hook, so we can't loop. The maintenance task list is
  // small and fixed; calling it per route is fine.
  const mongoStates = useMutationState({
    filters: { mutationKey: ["maintenance/mongo-migration"] },
    select: selectMutationState,
  });
  const cleanupStates = useMutationState({
    filters: { mutationKey: ["maintenance/local-cleanup"] },
    select: selectMutationState,
  });
  const compactDbStates = useMutationState({
    filters: { mutationKey: ["maintenance/compact-db"] },
    select: selectMutationState,
  });

  useEffect(() => {
    const statesByRoute = {
      "maintenance/mongo-migration": mongoStates,
      "maintenance/local-cleanup": cleanupStates,
      "maintenance/compact-db": compactDbStates,
    };
    for (const task of MAINTENANCE_TASKS) {
      const entries = statesByRoute[task.route];
      if (!entries || entries.length === 0) continue;
      const latest = entries[entries.length - 1];
      if (latest.status !== "success" && latest.status !== "error") continue;
      const lastShown = _lastShownByRoute.get(task.route);
      if (lastShown !== undefined && lastShown >= latest.submittedAt) continue;
      _lastShownByRoute.set(task.route, latest.submittedAt);
      if (latest.status === "success") {
        showAlert("success", task.formatSuccess(latest.data));
      } else {
        const error = latest.error;
        showAlert("error", error instanceof Error ? error.message : task.errorMessage);
      }
    }
  }, [mongoStates, cleanupStates, compactDbStates, showAlert]);

  return null;
}
