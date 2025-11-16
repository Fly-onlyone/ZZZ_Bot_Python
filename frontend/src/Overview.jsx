import React, { memo } from "react";
import { Box, Paper, Typography } from "@mui/material";
import Mission from "./content/Mission";
import RunningStatus from "./content/RunningStatus";
import Hunt from "./content/Hunt";
import { IconActivity, IconReportAnalytics, IconTarget } from "@tabler/icons-react";
import { COMMON_COLORS } from "./theme/colors";
import { TRANSITIONS } from "./theme/styles";
import { useThemeContext } from "./theme/ThemeContext";

// Memoized icon badge component to prevent unnecessary re-renders
const IconBadge = memo(({ icon, gradient, themeColors }) => (
  <Box
    sx={{
      width: 40,
      height: 40,
      borderRadius: "10px",
      background: gradient,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      boxShadow: `0 4px 14px ${themeColors.alpha.hover}`,
    }}
  >
    {icon}
  </Box>
));

export default function Overview() {
  const { themeColors } = useThemeContext();

  // Section card component
  const SectionCard = ({ title, icon, children, colorScheme = "primary" }) => {
    const isPrimary = colorScheme === "primary";
    const cardBg = isPrimary
      ? themeColors.gradients.backgroundSubtle
      : "linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)";
    const headerBg = isPrimary
      ? themeColors.gradients.header
      : "linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)";
    const borderColor = isPrimary
      ? themeColors.alpha.cardBorder
      : "rgba(16, 185, 129, 0.2)";
    const iconGradient = isPrimary
      ? themeColors.gradients.primary
      : "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)";

    return (
      <Paper
        elevation={0}
        sx={{
          borderRadius: "16px",
          background: cardBg,
          border: `1px solid ${borderColor}`,
          overflow: "hidden",
          transition: TRANSITIONS.default,
          "&:hover": {
            boxShadow: `0 8px 32px ${themeColors.alpha.hover}`,
            transform: "translateY(-2px)",
          },
        }}
      >
        <Box
          sx={{
            background: headerBg,
            borderBottom: `1px solid ${borderColor}`,
            padding: "20px 24px",
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <IconBadge icon={icon} gradient={iconGradient} themeColors={themeColors} />
          <Typography
            variant="h5"
            sx={{ fontWeight: 700, color: COMMON_COLORS.text.primary }}
          >
            {title}
          </Typography>
        </Box>
        <Box sx={{ padding: "24px" }}>{children}</Box>
      </Paper>
    );
  };

  return (
    <div className="space-y-6">
      <SectionCard
        title="Mission Report"
        icon={<IconReportAnalytics size={24} color="#ffffff" />}
        colorScheme="primary"
      >
        <Mission />
      </SectionCard>

      <SectionCard
        title="Hunt Mode"
        icon={<IconTarget size={24} color="#ffffff" />}
        colorScheme="primary"
      >
        <Hunt />
      </SectionCard>

      <SectionCard
        title="Running Status"
        icon={<IconActivity size={24} color="#ffffff" />}
        colorScheme="success"
      >
        <RunningStatus />
      </SectionCard>
    </div>
  );
}
