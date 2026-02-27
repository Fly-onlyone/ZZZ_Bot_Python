import React from "react";
import { AppBar, Box, Toolbar, Typography } from "@mui/material";
import zIndex from "@mui/material/styles/zIndex";
import { COMMON_COLORS } from "../../theme/colors";
import { TRANSITIONS } from "../../theme/styles";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * AppHeader Component
 *
 * Application header bar with logo and title.
 * Displayed at the top of the application with fixed positioning.
 */
export default function AppHeader() {
  const { themeColors } = useThemeContext();
  const Qingyi02 = "/Qingyi02.ico";

  return (
    <AppBar position="fixed" sx={{ zIndex: zIndex.drawer + 1 }}>
      <Toolbar className="relative flex items-center justify-center">
        {/* App Icon */}
        <div className="absolute left-4 flex items-center gap-2">
          <Box
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
              transition: TRANSITIONS.default,
              "&:hover": {
                transform: "scale(1.05)",
                boxShadow: `0 4px 20px ${themeColors.alpha.hover}`,
              },
            }}
          >
            <img src={Qingyi02} alt="ZZZ Bot Icon" className="h-10 w-10" />
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
          }}
        >
          ZZZ Bot
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
