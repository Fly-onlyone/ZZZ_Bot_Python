import { useState } from "react";
import { useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { DataLoader } from "../services";
import { logInfo, logWarn } from "../services/sentryLogger.js";

/**
 * useFormState Hook
 *
 * Manages form state for route-based data editing.
 * Handles data fetching, mutations, and optimistic updates via React Query.
 *
 * @returns {Object} Form state and handlers
 *   - value: Current form data
 *   - error: Fetch error if any
 *   - handleChange: Update a single field
 *   - handleSubmit: Save changes to backend
 *   - mutation: React Query mutation object
 *   - route: Current route name
 */
export function useFormState(routeOverride) {
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });

  const location = useLocation();
  const route = routeOverride || location.pathname.replace("/", "");
  const queryClient = useQueryClient();

  const { useRouteData, useSaveData } = DataLoader();
  const { data: value = {}, error } = useRouteData(route);
  const mutation = useSaveData(route);

  const handleChange = (key, newValue) => {
    queryClient.setQueryData([route], (prev) => ({
      ...prev,
      [key]: newValue,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(value, {
      onSuccess: () => {
        logInfo("Form save succeeded", {
          route,
        });
        setAlert({
          open: true,
          type: "success",
          message: "Data saved successfully!",
        });
      },
      onError: (saveError) => {
        logWarn("Form save failed in hook handler", {
          route,
          error: saveError instanceof Error ? saveError.message : String(saveError),
        });
        setAlert({
          open: true,
          type: "error",
          message: "Failed to save data.",
        });
      },
    });
  };

  return {
    value,
    error,
    handleChange,
    handleSubmit,
    mutation,
    route,
    alert,
    setAlert,
  };
}
