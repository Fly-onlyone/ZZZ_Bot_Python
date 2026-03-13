import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { BACKEND_URL } from "../config";
import { logInfo, logWarn } from "../services/sentryLogger.js";

const MIN_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;

/**
 * SSE hook that listens for backend task-completed events
 * and invalidates all cached queries so the UI refreshes immediately.
 *
 * @param {{ enabled: boolean }} options
 */
export default function useTaskEvents({ enabled = false } = {}) {
  const queryClient = useQueryClient();
  const reconnectDelay = useRef(MIN_RECONNECT_DELAY);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let es;
    let reconnectTimer;
    let disposed = false;

    function connect() {
      if (disposed) {
        return;
      }

      es = new EventSource(`${BACKEND_URL}/events`);

      es.onopen = () => {
        reconnectDelay.current = MIN_RECONNECT_DELAY;
        logInfo("SSE connection established");
      };

      es.addEventListener("task-completed", () => {
        logInfo("SSE task-completed received, invalidating queries");
        queryClient.invalidateQueries();
      });

      es.onerror = () => {
        es.close();
        if (disposed) {
          return;
        }

        logWarn("SSE connection lost, reconnecting", {
          delay: reconnectDelay.current,
        });

        reconnectTimer = setTimeout(() => {
          reconnectDelay.current = Math.min(
            reconnectDelay.current * 2,
            MAX_RECONNECT_DELAY
          );
          connect();
        }, reconnectDelay.current);
      };
    }

    connect();

    return () => {
      disposed = true;
      clearTimeout(reconnectTimer);
      if (es) {
        es.close();
      }
    };
  }, [enabled, queryClient]);
}
