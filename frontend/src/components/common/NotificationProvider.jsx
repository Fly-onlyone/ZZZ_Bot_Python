import React, { useCallback, useMemo, useState } from "react";
import { Alert, Snackbar } from "@mui/material";
import { motion } from "framer-motion";

import { NotificationContext } from "./NotificationContext";

/**
 * @typedef {{
 *   open: boolean,
 *   type: import("@mui/material").AlertColor,
 *   message: string,
 * }} NotificationState
 */

/**
 * App-level toast/snackbar. Lives above the router so notifications fire even
 * when the page that triggered them has unmounted (e.g. a long migration that
 * finishes while the user has navigated to a different tab).
 */
export default function NotificationProvider({ children }) {
  /** @type {[NotificationState, React.Dispatch<React.SetStateAction<NotificationState>>]} */
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });

  const showAlert = useCallback((type, message) => {
    setAlert({ open: true, type, message });
  }, []);

  const handleClose = useCallback((_event, reason) => {
    if (reason === "clickaway") return;
    setAlert((prev) => ({ ...prev, open: false }));
  }, []);

  const value = useMemo(() => ({ showAlert }), [showAlert]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <Snackbar
        open={alert.open}
        autoHideDuration={5000}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          transition={{ duration: 0.3 }}
        >
          <Alert severity={alert.type} variant="outlined">
            {alert.message}
          </Alert>
        </motion.div>
      </Snackbar>
    </NotificationContext.Provider>
  );
}
