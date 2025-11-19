import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  API_RETRY_COUNT,
  BACKEND_URL,
  DEFAULT_STALE_TIME,
  STALE_TIMES,
} from "../config";

export const DataLoader = () => {
  const queryClient = useQueryClient();

  const fetchAllRoutes = async () => {
    const response = await fetch(`${BACKEND_URL}/routes`);
    if (!response.ok) throw new Error("Failed to fetch routes");
    try {
      const data = await response.json();
      return data.routes || [];
    } catch (error) {
      throw new Error(`Failed to parse routes JSON: ${error.message}`);
    }
  };

  const fetchRouteData = async (route) => {
    const response = await fetch(`${BACKEND_URL}/${route}`);
    if (!response.ok) throw new Error(`Failed to fetch data for ${route}`);
    try {
      return await response.json();
    } catch (error) {
      throw new Error(`Failed to parse JSON for ${route}: ${error.message}`);
    }
  };

  const prefetchAllRoutes = async () => {
    const routes = await fetchAllRoutes();
    for (const route of routes) {
      queryClient.prefetchQuery({
        queryKey: [route],
        queryFn: () => fetchRouteData(route),
        staleTime: STALE_TIMES[route] || DEFAULT_STALE_TIME,
        retry: API_RETRY_COUNT,
      });
    }
  };

  const useRouteData = (route) => {
    return useQuery({
      queryKey: [route],
      queryFn: () => fetchRouteData(route),
      staleTime: STALE_TIMES[route] || DEFAULT_STALE_TIME,
      retry: API_RETRY_COUNT,
      refetchOnWindowFocus: false, // Prevent excessive refetching
    });
  };

  const useSaveData = (route) => {
    const saveData = async (newValue) => {
      const response = await fetch(`${BACKEND_URL}/${route}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newValue),
      });
      if (!response.ok) throw new Error("Failed to save data");
    };

    return useMutation({
      mutationFn: saveData,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: [route] });
      },
    });
  };

  return { prefetchAllRoutes, useRouteData, useSaveData };
};

// Re-export BACKEND_URL for convenience
export { BACKEND_URL } from "../config/constants";
