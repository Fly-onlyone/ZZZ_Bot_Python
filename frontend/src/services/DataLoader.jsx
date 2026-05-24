import { useCallback } from "react";
import { useIsMutating, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_RETRY_COUNT, BACKEND_URL, DEFAULT_STALE_TIME, STALE_TIMES } from "../config";
import { logError, logInfo, logWarn } from "./sentryLogger.js";

const STARTUP_RETRY_COUNT = 12;
const STARTUP_RETRY_DELAY_MS = 500;
const STARTUP_MAX_RETRY_DELAY_MS = 3000;
const RELATED_QUERY_KEYS_BY_ROUTE = {
  settings: [["settings"]],
  "locator-tracker/clear": [["locator-tracker"], ["locator-tracker/failures"]],
  "backup/import": [
    ["account"],
    ["shopping"],
    ["redeem"],
    ["settings"],
    ["overview/hunt"],
    ["overview/mission"],
    ["backup/summary"],
  ],
  "maintenance/mongo-migration": [
    ["account"],
    ["shopping"],
    ["settings"],
    ["overview/hunt"],
    ["backup/summary"],
  ],
};

const getStartupRetryDelay = (attemptIndex) =>
  Math.min(STARTUP_RETRY_DELAY_MS * 2 ** attemptIndex, STARTUP_MAX_RETRY_DELAY_MS);

export const DataLoader = () => {
  const queryClient = useQueryClient();

  const fetchJson = useCallback(async (url, context, options = {}) => {
    const {
      requestFailureSeverity = "error",
      requestFailureMessage = "Frontend API request failed",
    } = options;
    let response;

    try {
      response = await fetch(url);
    } catch (error) {
      const attributes = {
        context,
        url,
        phase: "request",
        error: error instanceof Error ? error.message : String(error),
      };
      if (requestFailureSeverity === "warn") {
        logWarn(requestFailureMessage, attributes);
      } else {
        logError(requestFailureMessage, error, attributes);
      }
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`${context}: ${message}`);
    }

    if (!response.ok) {
      logWarn("Frontend API request returned non-OK status", {
        context,
        url,
        status: response.status,
      });
      throw new Error(`${context}: HTTP ${response.status}`);
    }

    try {
      return await response.json();
    } catch (error) {
      logError("Frontend API response parsing failed", error, {
        context,
        url,
        phase: "parse",
      });
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`${context}: ${message}`);
    }
  }, []);

  const fetchRouteData = useCallback(
    async (route) => {
      const data = await fetchJson(`${BACKEND_URL}/${route}`, `Failed to fetch data for ${route}`);
      logInfo("Frontend route data loaded", {
        route,
      });
      return data;
    },
    [fetchJson]
  );

  const prefetchRouteData = useCallback(
    async (route) => {
      const data = await fetchJson(
        `${BACKEND_URL}/${route}`,
        `Failed to prefetch data for ${route}`,
        {
          requestFailureSeverity: "warn",
          requestFailureMessage: "Frontend route prefetch request failed",
        }
      );
      logInfo("Frontend route data prefetched", {
        route,
      });
      return data;
    },
    [fetchJson]
  );

  const prefetchRoutes = useCallback(
    async (routes) => {
      if (!Array.isArray(routes) || routes.length === 0) {
        return;
      }

      const uniqueRoutes = [...new Set(routes.filter(Boolean))];

      const results = await Promise.allSettled(
        uniqueRoutes.map((route) =>
          queryClient.prefetchQuery({
            queryKey: [route],
            queryFn: () => prefetchRouteData(route),
            staleTime: STALE_TIMES[route] || DEFAULT_STALE_TIME,
            retry: API_RETRY_COUNT,
          })
        )
      );

      const failedRoutes = results
        .map((result, index) => (result.status === "rejected" ? uniqueRoutes[index] : null))
        .filter(Boolean);

      if (failedRoutes.length > 0) {
        logWarn("Frontend route prefetch completed with failures", {
          routeCount: uniqueRoutes.length,
          failedRoutes,
        });
        return;
      }

      logInfo("Frontend route prefetch completed", {
        routeCount: uniqueRoutes.length,
      });
    },
    [prefetchRouteData, queryClient]
  );

  const useRouteData = (route, queryOptions = {}) => {
    return useQuery({
      queryKey: [route],
      queryFn: () => fetchRouteData(route),
      staleTime: STALE_TIMES[route] || DEFAULT_STALE_TIME,
      retry: API_RETRY_COUNT,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      ...queryOptions,
    });
  };

  const useBackendHealth = () => {
    return useQuery({
      queryKey: ["backend-health"],
      queryFn: () =>
        fetchJson(`${BACKEND_URL}/health`, "Backend unavailable", {
          requestFailureSeverity: "warn",
          requestFailureMessage: "Frontend backend health probe failed",
        }),
      staleTime: 1000 * 5,
      retry: STARTUP_RETRY_COUNT,
      retryDelay: getStartupRetryDelay,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    });
  };

  const useSaveData = (route) => {
    const saveData = async (newValue) => {
      logInfo("Frontend save requested", {
        route,
      });

      const response = await fetch(`${BACKEND_URL}/${route}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newValue),
      });

      if (!response.ok) {
        logWarn("Frontend save returned non-OK status", {
          route,
          status: response.status,
        });
        throw new Error("Failed to save data");
      }
    };

    const mutation = useMutation({
      mutationKey: ["save", route],
      mutationFn: saveData,
      onError: (error) => {
        logError("Frontend save failed", error, {
          route,
        });
      },
      onSuccess: async () => {
        logInfo("Frontend save completed", {
          route,
        });
        const relatedQueryKeys = RELATED_QUERY_KEYS_BY_ROUTE[route] || [[route]];
        await Promise.all(
          relatedQueryKeys.map((queryKey) => queryClient.invalidateQueries({ queryKey }))
        );
      },
    });

    // useMutation state is local to the component, so navigating away and back
    // resets isPending while the original save is still in flight. useIsMutating
    // reads the shared MutationCache and lets the new instance see it.
    const globalPendingCount = useIsMutating({ mutationKey: ["save", route] });

    return {
      ...mutation,
      isPending: mutation.isPending || globalPendingCount > 0,
    };
  };

  const useActionData = (route) => {
    const runAction = async (payload = {}) => {
      logInfo("Frontend action requested", {
        route,
      });

      const response = await fetch(`${BACKEND_URL}/${route}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const contentType = response.headers.get("content-type") || "";
      const responseData = contentType.includes("application/json") ? await response.json() : null;

      if (!response.ok) {
        const errorMessage =
          responseData?.error || responseData?.message || `Failed to run action for ${route}`;
        logWarn("Frontend action returned non-OK status", {
          route,
          status: response.status,
          errorMessage,
        });
        throw new Error(errorMessage);
      }

      return responseData;
    };

    const mutation = useMutation({
      mutationKey: [route],
      mutationFn: runAction,
      onSuccess: async () => {
        logInfo("Frontend action completed", {
          route,
        });
        const relatedQueryKeys = RELATED_QUERY_KEYS_BY_ROUTE[route];
        if (relatedQueryKeys) {
          await Promise.all(
            relatedQueryKeys.map((queryKey) => queryClient.invalidateQueries({ queryKey }))
          );
        }
      },
      onError: (error) => {
        logError("Frontend action failed", error, {
          route,
        });
      },
    });

    // useMutation state is local to the component, so navigating away and back
    // resets isPending while the original fetch is still in flight. useIsMutating
    // reads the shared MutationCache and lets the new instance see it.
    const globalPendingCount = useIsMutating({ mutationKey: [route] });

    return {
      ...mutation,
      isPending: mutation.isPending || globalPendingCount > 0,
    };
  };

  return {
    prefetchRoutes,
    useRouteData,
    useSaveData,
    useActionData,
    useBackendHealth,
  };
};

export { BACKEND_URL } from "../config/constants";
