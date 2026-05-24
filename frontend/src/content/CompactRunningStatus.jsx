import { Box, Paper, Typography } from "@mui/material";
import { motion } from "framer-motion";
import ScheduleIcon from "@mui/icons-material/Schedule";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PauseCircleOutlineIcon from "@mui/icons-material/PauseCircleOutline";
import { BACKEND_URL, DataLoader } from "../services/DataLoader";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      when: "beforeChildren",
    },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
};

const iconVariants = {
  hidden: { opacity: 0, scale: 0.8, rotate: -10 },
  visible: {
    opacity: 1,
    scale: 1,
    rotate: 0,
    transition: { type: "spring", stiffness: 200, damping: 15 },
  },
};

export default function CompactRunningStatus() {
  const { useRouteData } = DataLoader();
  const { themeColors } = useThemeContext();
  const { data: runStatus } = useRouteData("check-run-status");
  const { data: huntInfo } = useRouteData("overview/hunt");

  if (!runStatus) {
    return null;
  }

  const { last_run, next_run } = runStatus;
  const huntItems = Array.isArray(huntInfo?.["hunt_items"]) ? huntInfo["hunt_items"] : [];
  const huntActive = huntInfo?.enabled && huntItems.length > 0;

  const statCardSx = {
    p: 2.5,
    borderRadius: "12px",
    background: themeColors.gradients.backgroundSubtle,
    border: `1px solid ${themeColors.alpha.cardBorder}`,
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 1,
    transition: "all 0.3s ease-in-out",
    "&:hover": {
      boxShadow: `0 0 20px ${themeColors.glow}20`,
    },
  };

  return (
    <Paper
      component={motion.div}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{
        y: -5,
        scale: 1.02,
        transition: { duration: 0.2, ease: "easeOut" },
      }}
      elevation={0}
      sx={{
        borderRadius: "16px",
        background: themeColors.gradients.backgroundSubtle,
        border: `1px solid ${themeColors.alpha.cardBorder}`,
        overflow: "hidden",
        backdropFilter: "blur(12px)",
        cursor: "default",
        mb: 3,
        p: 3,
        display: "flex",
        alignItems: "center",
        gap: 3,
        "&:hover": {
          boxShadow: `0 0 25px ${themeColors.glow}20, 0 8px 30px ${themeColors.glow}10`,
          border: `1px solid ${themeColors.primary.main}60`,
        },
      }}
    >
      <motion.img
        src={`${BACKEND_URL}/images/Zhu Yuan02.ico`}
        alt="Zhu Yuan"
        variants={iconVariants}
        initial="hidden"
        animate="visible"
        whileHover={{ scale: 1.1, rotate: 5 }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        style={{
          width: 110,
          height: 110,
          flexShrink: 0,
          filter: `drop-shadow(0 0 10px ${themeColors.glow}50)`,
        }}
      />

      <Box
        component={motion.div}
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        sx={{
          flex: 1,
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 2,
        }}
      >
        <Paper component={motion.div} variants={cardVariants} elevation={2} sx={statCardSx}>
          <ScheduleIcon sx={{ color: themeColors.primary.main, fontSize: 32 }} />
          <Typography variant="body2" sx={{ color: COMMON_COLORS.text.muted, fontWeight: 600 }}>
            Last Run
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 700, color: themeColors.primary.light }}>
            {last_run || "—"}
          </Typography>
        </Paper>

        <Paper component={motion.div} variants={cardVariants} elevation={2} sx={statCardSx}>
          <ScheduleIcon sx={{ color: themeColors.secondary.main, fontSize: 32 }} />
          <Typography variant="body2" sx={{ color: COMMON_COLORS.text.muted, fontWeight: 600 }}>
            Next Run
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 700, color: themeColors.secondary.light }}>
            {next_run || "—"}
          </Typography>
        </Paper>

        <Paper component={motion.div} variants={cardVariants} elevation={2} sx={statCardSx}>
          {huntActive ? (
            <CheckCircleIcon sx={{ color: COMMON_COLORS.success.main, fontSize: 32 }} />
          ) : (
            <PauseCircleOutlineIcon sx={{ color: COMMON_COLORS.text.muted, fontSize: 32 }} />
          )}
          <Typography variant="body2" sx={{ color: COMMON_COLORS.text.muted, fontWeight: 600 }}>
            Hunt Status
          </Typography>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: huntActive ? COMMON_COLORS.success.light : COMMON_COLORS.text.muted,
            }}
          >
            {huntActive ? `${huntItems.length} Items` : "Disabled"}
          </Typography>
        </Paper>
      </Box>
    </Paper>
  );
}
