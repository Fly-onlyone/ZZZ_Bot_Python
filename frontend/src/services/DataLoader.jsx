import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  API_RETRY_COUNT,
  BACKEND_URL,
  DEFAULT_STALE_TIME,
  STALE_TIMES,
} from "../config";

export const DataLoader = () => {
  const queryClient = useQueryClient();

  const fetchJson = useCallback(async (url, context) => {
    let response;

    try {
      response = await fetch(url);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`${context}: ${message}`);
    }

    if (!response.ok) {
      throw new Error(`${context}: HTTP ${response.status}`);
    }

    try {
      return await response.json();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`${context}: ${message}`);
    }
  }, []);

  const fetchAllRoutes = useCallback(async () => {
    const data = await fetchJson(
      `${BACKEND_URL}/routes`,
      "Failed to fetch routes"
    );
    return Array.isArray(data?.routes) ? data.routes : [];
  }, [fetchJson]);

  const fetchRouteData = useCallback(
    async (route) => {
      return fetchJson(
        `${BACKEND_URL}/${route}`,
        `Failed to fetch data for ${route}`
      );
    },
    [fetchJson]
  );

  const prefetchAllRoutes = useCallback(async () => {
    let routes = [];

    try {
      routes = await fetchAllRoutes();
    } catch (error) {
      console.warn("Route prefetch skipped:", error);
      return;
    }

    await Promise.all(
      routes.map((route) =>
        queryClient
          .prefetchQuery({
            queryKey: [route],
            queryFn: () => fetchRouteData(route),
            staleTime: STALE_TIMES[route] || DEFAULT_STALE_TIME,
            retry: API_RETRY_COUNT,
          })
          .catch((error) => {
            console.warn(`Prefetch failed for ${route}:`, error);
          })
      )
    );
  }, [fetchAllRoutes, fetchRouteData, queryClient]);

  const useRouteData = (route) => {
    return useQuery({
      queryKey: [route],
      queryFn: () => fetchRouteData(route),
      staleTime: STALE_TIMES[route] || DEFAULT_STALE_TIME,
      retry: API_RETRY_COUNT,
      refetchOnWindowFocus: false,
    });
  };

  const useSaveData = (route) => {
    const saveData = async (newValue) => {
      const response = await fetch(`${BACKEND_URL}/${route}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newValue),
      });

      if (!response.ok) {
        throw new Error("Failed to save data");
      }
    };

    return useMutation({
      mutationFn: saveData,
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: [route] });
      },
    });
  };

  const useActionData = (route) => {
    const runAction = async (payload = {}) => {
      const response = await fetch(`${BACKEND_URL}/${route}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const contentType = response.headers.get("content-type") || "";
      const responseData = contentType.includes("application/json")
        ? await response.json()
        : null;

      if (!response.ok) {
        const errorMessage =
          responseData?.error ||
          responseData?.message ||
          `Failed to run action for ${route}`;
        throw new Error(errorMessage);
      }

      return responseData;
    };

    return useMutation({ mutationFn: runAction });
  };

  return { prefetchAllRoutes, useRouteData, useSaveData, useActionData };
};

export { BACKEND_URL } from "../config/constants";
