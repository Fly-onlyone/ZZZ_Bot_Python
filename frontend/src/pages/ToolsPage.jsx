import React, { useState } from "react";
import { Box, Tab, Tabs } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { IconCards } from "@tabler/icons-react";
import Logs from "./Logs";
import Backup from "./Backup";
import { ValueAdapter } from "../components";
import { DataLoader } from "../services";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";

const panelVariants = {
  initial: (direction) => ({
    opacity: 0,
    x: direction * 20,
    scale: 0.995,
  }),
  animate: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 140,
      damping: 22,
      mass: 0.9,
    },
  },
  exit: (direction) => ({
    opacity: 0,
    x: direction * -20,
    scale: 0.995,
    transition: {
      duration: 0.18,
      ease: "easeInOut",
    },
  }),
};

const monitoringTypeConfig = {
  sentry_traces_sample_rate: {
    type: "select",
    options: [
      { value: 1.0, label: "1.0 (Always)" },
      { value: 0.5, label: "0.5" },
      { value: 0.25, label: "0.25" },
      { value: 0.1, label: "0.1" },
    ],
  },
};

function formatCleanupSummary(report) {
  const deleted = report?.deleted || {};
  return (
    `Cleanup completed. Deleted ` +
    `${deleted["auth_storage_file"] || 0} auth file(s), ` +
    `${deleted["log_files"] || 0} log file(s), ` +
    `${deleted["screenshot_files"] || 0} screenshot file(s), ` +
    `${deleted["json_files"] || 0} JSON file(s).`
  );
}

function MonitoringPanel() {
  const { useActionData } = DataLoader();
  const cleanupMutation = useActionData("maintenance/local-cleanup");

  const handleRunCleanup = async () => {
    return cleanupMutation.mutateAsync({});
  };

  return (
    <ValueAdapter
      route="settings"
      customSections={{
        Monitoring: {
          icon: <IconCards />,
          fields: [
            "sentry_dsn",
            "sentry_frontend_dsn",
            "sentry_send_test_event",
            "sentry_traces_sample_rate",
          ],
        },
      }}
      typeConfig={monitoringTypeConfig}
      extraActions={[
        {
          key: "run-local-cleanup",
          label: "Run Local Cleanup",
          onClick: handleRunCleanup,
          successMessage: formatCleanupSummary,
          errorMessage: "Failed to run local cleanup.",
        },
      ]}
    />
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
        sx={{
          mb: 3,
          minHeight: 48,
          "& .MuiTabs-indicator": { display: "none" },
          "& .MuiTab-root": {
            minHeight: 48,
            minWidth: "auto",
            px: 2.5,
            color: COMMON_COLORS.text.muted,
            fontWeight: 600,
            textTransform: "none",
            position: "relative",
            "&::after": {
              content: '""',
              position: "absolute",
              left: 12,
              right: 12,
              bottom: 0,
              height: 3,
              borderRadius: "999px",
              backgroundColor: "transparent",
              transition: "background-color 0.2s ease",
            },
            "&.Mui-selected": {
              color: themeColors.primary.light,
            },
            "&.Mui-selected::after": {
              backgroundColor: themeColors.primary.main,
            },
          },
        }}
      >
        <Tab label="Logs" />
        <Tab label="Backup" />
        <Tab label="Monitoring" />
      </Tabs>

      <AnimatePresence mode="wait" initial={false} custom={tabDirection}>
        <Box
          key={activeTab}
          component={motion.div}
          custom={tabDirection}
          variants={panelVariants}
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
          {activeTab === 0 && <Logs />}
          {activeTab === 1 && <Backup />}
          {activeTab === 2 && <MonitoringPanel />}
        </Box>
      </AnimatePresence>
    </Box>
  );
}
