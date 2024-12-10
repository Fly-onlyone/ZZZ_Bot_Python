import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";

const STALE_TIME = 1000 * 60 * 1;

export const DataLoader = (BACKEND_URL = "http://127.0.0.1:8000") => {
  const queryClient = useQueryClient();

  const fetchAllRoutes = async () => {
    const response = await fetch(`${BACKEND_URL}/routes`);
    if (!response.ok) throw new Error("Failed to fetch routes");
    const data = await response.json();
    return data.routes || []; // Assuming backend returns { routes: [...] }
  };

  const fetchRouteData = async (route) => {
    const response = await fetch(`${BACKEND_URL}/${route}`);
    if (!response.ok) throw new Error(`Failed to fetch data for ${route}`);
    return response.json();
  };

  const prefetchAllRoutes = async () => {
    const routes = await fetchAllRoutes();
    for (const route of routes) {
      queryClient.prefetchQuery({
        queryKey: [route],
        queryFn: () => fetchRouteData(route),
        staleTime: STALE_TIME,
      });
    }
  };

  const useRouteData = (route) => {
    return useQuery({
      queryKey: [route],
      queryFn: () => fetchRouteData(route),
      staleTime: STALE_TIME,
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
