import { createContext, useContext } from "react";

export const NotificationContext = createContext({
  /**
   * @param {import("@mui/material").AlertColor} _type
   * @param {string} _message
   */
  showAlert: (_type, _message) => undefined,
});

export function useNotification() {
  return useContext(NotificationContext);
}
