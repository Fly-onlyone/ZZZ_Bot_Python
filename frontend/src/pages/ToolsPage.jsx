import React, { useState } from "react";
import { Box, CircularProgress, Tab, Tabs, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useThemeContext } from "../theme/ThemeContext";
import { getAuroraTabsStyles, auroraPanelVariants } from "../theme/tabStyles";

const LazyLogs = React.lazy(() => import("./Logs.jsx"));
const LazyBackup = React.lazy(() => import("./Backup.jsx"));
const LazyMonitoringPage = React.lazy(() => import("./MonitoringPage.jsx"));
const LazyLocatorTracker = React.lazy(() => import("./LocatorTracker.jsx"));

function TabFallback() {
  return (
    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
      }}
    >
      <CircularProgress size={28} />
      <Typography variant="body2" color="text.secondary">
        Loading tool panel...
      </Typography>
    </Box>
  );
}

export default function ToolsPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [tabDirection, setTabDirection] = useState(1);
  const { themeColors } = useThemeContext();

  const handleTabChange = (_, newValue) => {
    setTabDirection(newValue >= activeTab ? 1 : -1);
    setActiveTab(newValue);
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        height: "100%",
      }}
    >
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        centered
        sx={getAuroraTabsStyles(themeColors)}
      >
        <Tab label="Logs" />
        <Tab label="Backup" />
        <Tab label="Monitoring" />
        <Tab label="Locator" />
      </Tabs>

      <AnimatePresence mode="wait" initial={false} custom={tabDirection}>
        <Box
          key={activeTab}
          component={motion.div}
          custom={tabDirection}
          variants={auroraPanelVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          sx={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <React.Suspense fallback={<TabFallback />}>
            {activeTab === 0 && <LazyLogs />}
            {activeTab === 1 && <LazyBackup />}
            {activeTab === 2 && <LazyMonitoringPage />}
            {activeTab === 3 && <LazyLocatorTracker />}
          </React.Suspense>
        </Box>
      </AnimatePresence>
    </Box>
  );
}
