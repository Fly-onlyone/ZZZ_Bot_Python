import React, { useMemo, useState } from "react";
import {
  AppBar,
  Box,
  Button,
  Chip,
  IconButton,
  Popover,
  Toolbar,
  Typography,
} from "@mui/material";
import zIndex from "@mui/material/styles/zIndex";
import { keyframes } from "@mui/system";
import { motion } from "framer-motion";
import MenuIcon from "@mui/icons-material/Menu";
import { COMMON_COLORS } from "../../theme/colors";
import { GLOW, TRANSITIONS } from "../../theme/styles";
import { useThemeContext } from "../../theme/ThemeContext";
import { useZoom } from "../../hooks/useZoom.jsx";
import ThemePicker from "./ThemePicker";

function ZoomChip({ zoomPercent, onRestore }) {
  const [anchorEl, setAnchorEl] = useState(null);

  const handleClick = (event) => setAnchorEl(event.currentTarget);
  const handleClose = () => setAnchorEl(null);
  const handleRestore = () => {
    onRestore();
    handleClose();
  };

  return (
    <>
      <Chip
        label={`${zoomPercent}%`}
        size="small"
        onClick={handleClick}
        sx={{
          cursor: "pointer",
          color: COMMON_COLORS.text.secondary,
          borderColor: COMMON_COLORS.background.slate,
          fontSize: "0.75rem",
        }}
        variant="outlined"
      />
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        transformOrigin={{ vertical: "top", horizontal: "center" }}
        slotProps={{
          paper: {
            sx: {
              mt: 1,
              p: 1.5,
              background: COMMON_COLORS.background.paper,
              border: `1px solid ${COMMON_COLORS.background.slate}`,
            },
          },
        }}
      >
        <Button size="small" variant="outlined" onClick={handleRestore}>
          Restore to 100%
        </Button>
      </Popover>
    </>
  );
}

/**
 * AppHeader Component
 *
 * Application header bar with logo, title, theme picker, and zoom indicator.
 * Shows hamburger menu on mobile.
 */
export default function AppHeader({ isMobile = false, onMenuClick }) {
  const { themeColors, prefersReducedMotion } = useThemeContext();
  const { zoomLevel, resetZoom } = useZoom();
  const Qingyi02 = "/Qingyi02.ico";
  const zoomPercent = Math.round(zoomLevel * 100);

  const iconGlow = useMemo(
    () => keyframes`
      0%, 100% { box-shadow: ${GLOW.subtle(themeColors.glow)}; }
      50% { box-shadow: ${GLOW.strong(themeColors.glow)}; }
    `,
    [themeColors.glow]
  );

  return (
    <AppBar position="fixed" sx={{ zIndex: zIndex.drawer + 1 }}>
      <Toolbar className="relative flex items-center justify-center">
        {/* Left: Hamburger (mobile) or App Icon (desktop) */}
        <div className="absolute left-4 flex items-center gap-2">
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="Open navigation menu"
              edge="start"
              onClick={onMenuClick}
              sx={{ color: COMMON_COLORS.text.primary }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Box
            component={motion.div}
            whileHover={{
              scale: 1.15,
              rotate: [0, -5, 5, -3, 0],
              transition: { duration: 0.4, ease: "easeOut" },
            }}
            whileTap={{ scale: 0.95 }}
            sx={{
              width: 48,
              height: 48,
              borderRadius: "12px",
              padding: "4px",
              background: themeColors.gradients.header,
              border: `1px solid ${themeColors.alpha.cardBorder}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              animation: prefersReducedMotion
                ? "none"
                : `${iconGlow} 3s ease-in-out infinite`,
              "&:hover": {
                border: `1px solid ${themeColors.glow}60`,
              },
            }}
          >
            <motion.img
              src={Qingyi02}
              alt="ZZZ Bot Icon"
              className="h-10 w-10"
              whileHover={{
                filter: `drop-shadow(0 0 12px ${themeColors.glow}80)`,
              }}
            />
          </Box>
        </div>

        {/* App Title */}
        <Typography
          variant="h6"
          noWrap
          component="div"
          sx={{
            fontWeight: 700,
            color: COMMON_COLORS.text.primary,
            letterSpacing: "0.5px",
            textShadow: GLOW.text(themeColors.glow),
          }}
        >
          ZZZ Bot
        </Typography>

        {/* Right Controls */}
        <Box
          sx={{
            position: "absolute",
            right: 16,
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          {zoomPercent !== 100 && (
            <ZoomChip zoomPercent={zoomPercent} onRestore={resetZoom} />
          )}
          <ThemePicker />
        </Box>
      </Toolbar>
    </AppBar>
  );
}
