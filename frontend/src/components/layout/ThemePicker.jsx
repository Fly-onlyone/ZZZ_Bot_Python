import React, { useState } from "react";
import {
  Box,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Tooltip,
} from "@mui/material";
import PaletteIcon from "@mui/icons-material/Palette";
import CheckIcon from "@mui/icons-material/Check";
import { THEME_COLORS } from "../../theme/themes";
import { useThemeContext } from "../../theme/ThemeContext";
import { DataLoader } from "../../services";
import { COMMON_COLORS } from "../../theme/colors";

const THEMES = [
  { value: "nebula", label: "Nebula" },
  { value: "venom", label: "Venom" },
  { value: "glacier", label: "Glacier" },
  { value: "cyber", label: "Cyber" },
];

export default function ThemePicker() {
  const { themeName, themeColors, changeTheme } = useThemeContext();
  const { useBackendHealth, useSaveData, useRouteData } = DataLoader();
  const { data: healthData } = useBackendHealth();
  const isBackendReady = healthData?.status === "ok";
  const saveMutation = useSaveData("settings");
  const { data: settings = {} } = useRouteData("settings", {
    enabled: isBackendReady,
    retry: 6,
    retryDelay: (attemptIndex) => Math.min(500 * 2 ** attemptIndex, 3000),
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
  const [anchorEl, setAnchorEl] = useState(null);

  const handleOpen = (event) => setAnchorEl(event.currentTarget);
  const handleClose = () => setAnchorEl(null);

  const handleSelect = (name) => {
    if (!isBackendReady) {
      return;
    }
    changeTheme(name);
    handleClose();
    saveMutation.mutate({ ...settings, theme: name });
  };

  return (
    <>
      <Tooltip title="Theme">
        <span>
          <IconButton
            onClick={handleOpen}
            disabled={!isBackendReady}
            sx={{ color: themeColors.primary.light }}
          >
            <PaletteIcon />
          </IconButton>
        </span>
      </Tooltip>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        slotProps={{
          paper: {
            sx: {
              mt: 1,
              minWidth: 160,
              background: COMMON_COLORS.background.paper,
              border: `1px solid ${COMMON_COLORS.background.slate}`,
            },
          },
        }}
      >
        {THEMES.map(({ value, label }) => (
          <MenuItem
            key={value}
            selected={value === themeName}
            onClick={() => handleSelect(value)}
          >
            <ListItemIcon>
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  borderRadius: "50%",
                  background: THEME_COLORS[value].primary.main,
                  border: "2px solid",
                  borderColor:
                    value === themeName
                      ? COMMON_COLORS.text.primary
                      : "transparent",
                }}
              />
            </ListItemIcon>
            <ListItemText>{label}</ListItemText>
            {value === themeName && (
              <CheckIcon fontSize="small" sx={{ ml: 1, opacity: 0.7 }} />
            )}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
