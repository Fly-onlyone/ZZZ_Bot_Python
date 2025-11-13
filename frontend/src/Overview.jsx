import React, { memo } from "react";
import { Box, Paper, Typography } from "@mui/material";
import Mission from "./content/Mission";
import RunningStatus from "./content/RunningStatus";
import Hunt from "./content/Hunt";
import { IconActivity, IconReportAnalytics, IconTarget } from "@tabler/icons-react";
import { ALPHA, COLORS, GRADIENTS } from "./theme/colors";
import { cardStyles } from "./theme/styles";

// Memoized icon badge component to prevent unnecessary re-renders
const IconBadge = memo(({ icon, gradient }) => (
  <Box
    sx={{
      width: 40,
      height: 40,
      borderRadius: "10px",
      background: gradient,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      boxShadow: "0 4px 14px rgba(139, 92, 246, 0.4)",
    }}
  >
    {icon}
  </Box>
));

export default function Overview() {

  // Section card component
  const SectionCard = ({ title, icon, children, colorScheme = "primary" }) => {
    const isPrimary = colorScheme === "primary";
    const cardBg = isPrimary
      ? GRADIENTS.backgroundSubtle
      : "linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)";
    const headerBg = isPrimary
      ? GRADIENTS.header
      : "linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)";
    const borderColor = isPrimary
      ? ALPHA.cardBorder
      : "rgba(16, 185, 129, 0.2)";
    const iconGradient = isPrimary
      ? GRADIENTS.primary
      : "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)";

    return (
      <Paper
        elevation={0}
        sx={{
          ...cardStyles.default,
          background: cardBg,
          border: `1px solid ${borderColor}`,
        }}
      >
        <Box
          sx={{
            ...cardStyles.header,
            background: headerBg,
            borderBottom: `1px solid ${borderColor}`,
          }}
        >
          <IconBadge icon={icon} gradient={iconGradient} />
          <Typography
            variant="h5"
            sx={{ fontWeight: 700, color: COLORS.text.primary }}
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
