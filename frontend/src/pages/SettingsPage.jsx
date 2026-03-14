import React, { useEffect, useState } from "react";
import { Alert, Box, Tab, Tabs } from "@mui/material";
import { FormControlLabel, Switch } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import TaskIcon from "@mui/icons-material/Task";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import TuneIcon from "@mui/icons-material/Tune";
import { enable, disable, isEnabled } from "@tauri-apps/plugin-autostart";
import { SettingsSkeleton, ValueAdapter } from "../components";
import { BACKEND_URL } from "../config";
import { DataLoader } from "../services";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";

const settingsPanelVariants = {
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

const reducedMotionPanelVariants = {
  initial: {
    opacity: 0,
  },
  animate: {
    opacity: 1,
    transition: {
      duration: 0.12,
      ease: "easeOut",
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: 0.08,
      ease: "easeInOut",
    },
  },
};

const settingsTypeConfig = {
  run_task: {
    label: "Enable automatic runs (master switch)",
  },
  show_window_on_startup: {
    label: "Show window on startup",
  },
  theme: {
    type: "select",
    options: [
      { value: "nebula", label: "Nebula" },
      { value: "venom", label: "Venom" },
      { value: "glacier", label: "Glacier" },
      { value: "cyber", label: "Cyber" },
    ],
  },
  hunt_poll_max_wait_seconds: {
    type: "select",
    options: [
      { value: 60, label: "60s" },
      { value: 120, label: "120s" },
      { value: 180, label: "180s (Default)" },
      { value: 300, label: "300s" },
    ],
  },
  hunt_poll_interval_seconds: {
    type: "select",
    options: [
      { value: 1, label: "1s (Default)" },
      { value: 2, label: "2s" },
      { value: 3, label: "3s" },
      { value: 5, label: "5s" },
    ],
  },
};

function AutostartToggle() {
  const { useRouteData } = DataLoader();
  const { data: settings = {} } = useRouteData("settings");
  const [enabled, setEnabled] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const persistedPreference = settings?.autostart_on_login;
    if (typeof persistedPreference === "boolean") {
      setEnabled(persistedPreference);
      setLoaded(true);
      return;
    }

    let isMounted = true;
    isEnabled()
      .then((value) => {
        if (!isMounted) {
          return;
        }
        setEnabled(value);
        setLoaded(true);
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setLoaded(true);
      });

    return () => {
      isMounted = false;
    };
  }, [settings?.autostart_on_login]);

  const persistPreference = async (checked) => {
    const response = await fetch(`${BACKEND_URL}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ autostart_on_login: checked }),
    });

    if (!response.ok) {
      throw new Error("Failed to save auto-start preference.");
    }
  };

  const handleChange = async (event) => {
    const checked = event.target.checked;
    setSaving(true);
    try {
      if (checked) {
        await enable();
      } else {
        await disable();
      }

      try {
        await persistPreference(checked);
        setEnabled(checked);
      } catch {
        if (checked) {
          await disable().catch(() => {});
        } else {
          await enable().catch(() => {});
        }
      }
    } catch {
      // Ignore — running in browser dev mode without Tauri
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ mt: 2, px: 1 }}>
      <FormControlLabel
        control={
          <Switch
            checked={enabled}
            disabled={!loaded || saving}
            onChange={handleChange}
          />
        }
        label="Auto-start on Login"
      />
    </Box>
  );
}

const TAB_CONFIGS = [
  {
    label: "General",
    sections: {
      General: {
        icon: <TaskIcon />,
        fields: [
          "schedule_times",
          "run_task",
          "hide_browser",
          "show_window_on_startup",
          "exit_after_run",
          "theme",
        ],
      },
    },
    showAutostart: true,
  },
  {
    label: "Tasks",
    sections: {
      Tasks: {
        icon: <ShoppingCartIcon />,
        fields: [
          "gather_shopping_data",
          "exchange_good",
          "buy_all",
          "draw_item",
          "stop_on_failed_exchange",
        ],
      },
    },
  },
  {
    label: "Hunt",
    sections: {
      "Hunt Mode": {
        icon: <TuneIcon />,
        fields: [
          "enable_hunt_mode",
          "hunt_poll_max_wait_seconds",
          "hunt_poll_interval_seconds",
          "hunt_poll_backoff_enabled",
          "hunt_early_exit_on_unavailable",
        ],
      },
    },
  },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [tabDirection, setTabDirection] = useState(1);
  const { themeColors, prefersReducedMotion } = useThemeContext();
  const { useRouteData } = DataLoader();
  const { data: settings, isLoading } = useRouteData("settings");
  const resolvedSettings = settings || {};
  const isAutomationOff = resolvedSettings.run_task === false;
  const isAffectedTab = activeTab === 1 || activeTab === 2;
  const panelVariants = prefersReducedMotion
    ? reducedMotionPanelVariants
    : settingsPanelVariants;

  const handleTabChange = (_, newValue) => {
    setTabDirection(newValue >= activeTab ? 1 : -1);
    setActiveTab(newValue);
  };

  if (isLoading && !settings) {
    return <SettingsSkeleton />;
  }

  const tabConfig = TAB_CONFIGS[activeTab];

  /** @type {import("react").ReactNode[]} */
  const tabItems = TAB_CONFIGS.map((tab) => (
    <Tab key={tab.label} label={tab.label} />
  ));

  return (
    <Box>
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        centered
        sx={{
          mb: 3,
          minHeight: 48,
          "& .MuiTabs-indicator": {
            display: "none",
          },
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
        {tabItems}
      </Tabs>

      <AnimatePresence mode="wait" initial={false} custom={tabDirection}>
        <Box
          key={tabConfig.label}
          component={motion.div}
          custom={tabDirection}
          variants={panelVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          {isAutomationOff && isAffectedTab && (
            <Alert severity="info" sx={{ mb: 2, borderRadius: "12px" }}>
              Automatic runs are disabled. These settings will apply when you
              re-enable automation in the General tab.
            </Alert>
          )}
          <Box
            sx={
              isAutomationOff && isAffectedTab
                ? { opacity: 0.5, pointerEvents: "none" }
                : undefined
            }
          >
            <ValueAdapter
              key={activeTab}
              customSections={tabConfig.sections}
              typeConfig={settingsTypeConfig}
            />
          </Box>
          {tabConfig.showAutostart && <AutostartToggle />}
        </Box>
      </AnimatePresence>
    </Box>
  );
}
