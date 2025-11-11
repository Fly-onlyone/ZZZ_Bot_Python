import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// Route-specific stale times for optimal caching
const STALE_TIMES = {
  shopping: 1000 * 60 * 15,    // 15 minutes (changes hourly)
  redeem: 1000 * 60 * 10,      // 10 minutes
  settings: 1000 * 60 * 60,    // 1 hour (rarely changes)
  account: 1000 * 60 * 30,     // 30 minutes
  "overview/mission": 1000 * 60 * 5, // 5 minutes
};
const DEFAULT_STALE_TIME = 1000 * 60 * 1; // 1 minute fallback

export const BACKEND_URL = "http://127.0.0.1:8000";

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
        retry: 2, // Retry failed requests twice
      });
    }
  };

  const useRouteData = (route) => {
    return useQuery({
      queryKey: [route],
      queryFn: () => fetchRouteData(route),
      staleTime: STALE_TIMES[route] || DEFAULT_STALE_TIME,
      retry: 2, // Retry failed requests twice
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
