import React from "react";
import { Alert, Box, Chip, Paper, Typography } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { BACKEND_URL, DataLoader } from "../services/DataLoader";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";
import { MissionSkeleton } from "../components";

// Animation variants
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

const tableRowVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (index) => ({
    opacity: 1,
    x: 0,
    transition: {
      delay: index * 0.05,
      type: "spring",
      stiffness: 100,
      damping: 15,
    },
  }),
};

const imageVariants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: { duration: 0.2 },
  },
};

export default function Mission() {
  const { useRouteData } = DataLoader();
  const { themeColors } = useThemeContext();

  // Use the DataLoader's useRouteData hook
  const { data: mission, error } = useRouteData("overview/mission");
  if (error) {
    return (
      <Alert severity="error">
        Failed to fetch mission data: {error.message}
      </Alert>
    );
  }

  if (!mission) {
    return <MissionSkeleton />;
  }
  const { day, check_in, missions } = mission;
  if (!missions) {
    return <Alert severity="error">Today task hasn't done yet</Alert>;
  }

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants}>
      <Box
        component={motion.div}
        variants={containerVariants}
        sx={{ mb: 3, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}
      >
        <Paper
          component={motion.div}
          variants={cardVariants}
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background: themeColors.gradients.backgroundSubtle,
            border: `1px solid ${themeColors.alpha.cardBorder}`,
            textAlign: "center",
          }}
        >
          <Typography
            variant="body2"
            sx={{
              color: COMMON_COLORS.text.muted,
              fontWeight: 600,
              mb: 1,
              display: "block",
            }}
          >
            Current Day
          </Typography>
          <Typography
            variant="h4"
            sx={{ fontWeight: 700, color: themeColors.primary.light }}
          >
            {day}
          </Typography>
        </Paper>
        <Paper
          component={motion.div}
          variants={cardVariants}
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background:
              check_in === "Login Success"
                ? `linear-gradient(135deg, ${COMMON_COLORS.success.main}1A 0%, ${COMMON_COLORS.success.dark}1A 100%)`
                : `linear-gradient(135deg, ${COMMON_COLORS.error.main}1A 0%, ${COMMON_COLORS.error.dark}1A 100%)`,
            border: `1px solid ${
              check_in === "Login Success"
                ? `${COMMON_COLORS.success.main}4D`
                : `${COMMON_COLORS.error.main}4D`
            }`,
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1,
          }}
        >
          {check_in === "Login Success" ? (
            <CheckCircleIcon
              sx={{ color: COMMON_COLORS.success.main, fontSize: 32 }}
            />
          ) : (
            <ErrorIcon sx={{ color: COMMON_COLORS.error.main, fontSize: 32 }} />
          )}
          <Typography
            variant="body1"
            sx={{
              fontWeight: 600,
              color:
                check_in === "Login Success"
                  ? COMMON_COLORS.success.light
                  : COMMON_COLORS.error.light,
            }}
          >
            {check_in}
          </Typography>
        </Paper>
      </Box>

      <AnimatePresence mode="wait">
        {check_in === "Login Success" && (
          <Box
            component={motion.div}
            key="login-reward"
            variants={imageVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            sx={{
              my: 3,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <Paper
              elevation={0}
              sx={{
                borderRadius: "12px",
                overflow: "hidden",
                border: `1px solid ${COMMON_COLORS.success.main}33`,
                boxShadow: `0 4px 20px ${COMMON_COLORS.success.main}26`,
              }}
            >
              <img
                src={`${BACKEND_URL}/screenshot/login_reward.png`}
                alt="Login Reward"
                style={{ display: "block", maxWidth: "100%" }}
              />
            </Paper>
          </Box>
        )}
      </AnimatePresence>

      <Typography
        variant="h6"
        sx={{
          mb: 2,
          fontWeight: 600,
          color: COMMON_COLORS.text.tertiary,
        }}
      >
        Mission Status
      </Typography>
      <Box
        sx={{
          borderRadius: "12px",
          overflow: "hidden",
          border: `1px solid ${themeColors.alpha.divider}`,
        }}
      >
        <Box
          component="table"
          sx={{
            width: "100%",
            borderCollapse: "collapse",
          }}
        >
          <Box
            component="thead"
            sx={{
              background: themeColors.gradients.header,
            }}
          >
            <Box component="tr">
              <Box
                component="th"
                sx={{
                  px: 3,
                  py: 2,
                  textAlign: "left",
                  fontWeight: 600,
                  color: COMMON_COLORS.text.secondary,
                  borderBottom: `1px solid ${themeColors.alpha.divider}`,
                }}
              >
                Mission
              </Box>
              <Box
                component="th"
                sx={{
                  px: 3,
                  py: 2,
                  textAlign: "left",
                  fontWeight: 600,
                  color: COMMON_COLORS.text.secondary,
                  borderBottom: `1px solid ${themeColors.alpha.divider}`,
                }}
              >
                Status
              </Box>
            </Box>
          </Box>
          <Box component="tbody">
            {missions.map((mission, index) => (
              <Box
                component={motion.tr}
                key={index}
                custom={index}
                variants={tableRowVariants}
                initial="hidden"
                animate="visible"
                sx={{
                  background:
                    mission.state === "Finished"
                      ? `${COMMON_COLORS.success.main}14`
                      : `${COMMON_COLORS.error.main}14`,
                  transition: "all 0.2s ease-in-out",
                  "&:hover": {
                    background:
                      mission.state === "Finished"
                        ? `${COMMON_COLORS.success.main}26`
                        : `${COMMON_COLORS.error.main}26`,
                  },
                  borderBottom:
                    index !== missions.length - 1
                      ? `1px solid ${themeColors.alpha.card}`
                      : "none",
                }}
              >
                <Box
                  component="td"
                  sx={{
                    px: 3,
                    py: 2,
                    color: COMMON_COLORS.text.tertiary,
                  }}
                >
                  {mission.name}
                </Box>
                <Box
                  component="td"
                  sx={{
                    px: 3,
                    py: 2,
                  }}
                >
                  <Chip
                    label={mission.state}
                    size="small"
                    icon={
                      mission.state === "Finished" ? (
                        <CheckCircleIcon
                          sx={{
                            color: `${COMMON_COLORS.success.main} !important`,
                          }}
                        />
                      ) : (
                        <ErrorIcon
                          sx={{
                            color: `${COMMON_COLORS.error.main} !important`,
                          }}
                        />
                      )
                    }
                    sx={{
                      background:
                        mission.state === "Finished"
                          ? `${COMMON_COLORS.success.main}33`
                          : `${COMMON_COLORS.error.main}33`,
                      color:
                        mission.state === "Finished"
                          ? COMMON_COLORS.success.light
                          : COMMON_COLORS.error.light,
                      fontWeight: 600,
                      border: `1px solid ${
                        mission.state === "Finished"
                          ? `${COMMON_COLORS.success.main}4D`
                          : `${COMMON_COLORS.error.main}4D`
                      }`,
                    }}
                  />
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}
