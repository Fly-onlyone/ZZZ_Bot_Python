import { Alert, Box, Chip, Paper, Typography } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { DataLoader } from "../services";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import { DateTimeField } from "@mui/x-date-pickers";
import dayjs from "dayjs";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";
import SearchOffIcon from "@mui/icons-material/SearchOff";
import PauseCircleOutlineIcon from "@mui/icons-material/PauseCircleOutline";
import { EmptyState, HuntSkeleton } from "../components";

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

const scheduleBoxVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: { duration: 0.2 },
  },
};

const isPendingOrUnavailableSchedule = (scheduledTime) =>
  scheduledTime === "Not scheduled" ||
  scheduledTime === "Invalid time" ||
  scheduledTime === "Pending sync";

export default function Hunt() {
  const { useRouteData } = DataLoader();
  const { themeColors } = useThemeContext();

  // Use the DataLoader's useRouteData hook
  const { data: huntInfo, error } = useRouteData("overview/hunt");

  if (error) {
    return <Alert severity="error">Failed to fetch hunt data: {error.message}</Alert>;
  }

  if (!huntInfo) {
    return <HuntSkeleton />;
  }

  const { enabled, hunt_items, next_hunt_time } = huntInfo;

  // If hunt mode is disabled
  if (!enabled) {
    return (
      <EmptyState
        icon={<PauseCircleOutlineIcon />}
        title="Hunt Mode Disabled"
        subtitle="Enable hunt mode in Settings to start hunting for items when the shop renews."
      />
    );
  }

  // If hunt mode is enabled but no items
  if (!hunt_items || hunt_items.length === 0) {
    return (
      <EmptyState
        icon={<SearchOffIcon />}
        title="No Items Being Hunted"
        subtitle="Hunt mode is active but no items are marked for hunting. Add items to hunt on the Shopping page."
      />
    );
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
            background: `linear-gradient(135deg, ${COMMON_COLORS.success.main}1A 0%, ${COMMON_COLORS.success.dark}1A 100%)`,
            border: `1px solid ${COMMON_COLORS.success.main}4D`,
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1,
            backdropFilter: "blur(8px)",
          }}
        >
          <CheckCircleIcon sx={{ color: COMMON_COLORS.success.main, fontSize: 32 }} />
          <Typography variant="body1" sx={{ fontWeight: 600, color: COMMON_COLORS.success.light }}>
            Hunt Mode Active
          </Typography>
        </Paper>
        <Paper
          component={motion.div}
          variants={cardVariants}
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background: `linear-gradient(135deg, ${COMMON_COLORS.warning.main}1A 0%, ${COMMON_COLORS.warning.dark}1A 100%)`,
            border: `1px solid ${COMMON_COLORS.warning.main}4D`,
            textAlign: "center",
            backdropFilter: "blur(8px)",
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
            Items Hunting
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 700, color: COMMON_COLORS.warning.light }}>
            {hunt_items.length}
          </Typography>
        </Paper>
      </Box>

      <AnimatePresence mode="wait">
        {next_hunt_time && (
          <Box
            component={motion.div}
            key="next-hunt-time"
            variants={scheduleBoxVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            sx={{
              mb: 3,
              p: 3,
              borderRadius: "12px",
              background: themeColors.gradients.backgroundSubtle,
              border: `1px solid ${themeColors.alpha.divider}`,
              display: "flex",
              alignItems: "center",
              gap: 2,
            }}
          >
            <AccessTimeIcon sx={{ color: themeColors.primary.main, fontSize: 28 }} />
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, color: COMMON_COLORS.text.tertiary }}>
                Next Hunt Scheduled:
              </Typography>
              <DateTimeField
                defaultValue={dayjs(next_hunt_time, "HH:mm DD/MM/YY")}
                format="DD/MM/YYYY - hh:mm A"
              />
            </Box>
          </Box>
        )}
      </AnimatePresence>

      <Typography
        variant="h6"
        sx={{
          mb: 2,
          fontWeight: 600,
          color: COMMON_COLORS.text.secondary,
        }}
      >
        Items Being Hunted
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
                  textShadow: `0 0 15px ${themeColors.glow}20`,
                }}
              >
                #
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
                  textShadow: `0 0 15px ${themeColors.glow}20`,
                }}
              >
                Item Name
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
                  textShadow: `0 0 15px ${themeColors.glow}20`,
                }}
              >
                Scheduled Hunt Time
              </Box>
            </Box>
          </Box>
          <Box component="tbody">
            {hunt_items.map((item, index) => {
              const isNeutralSchedule = isPendingOrUnavailableSchedule(item.scheduled_time);

              return (
                <Box
                  component={motion.tr}
                  key={index}
                  custom={index}
                  variants={tableRowVariants}
                  initial="hidden"
                  animate="visible"
                  sx={{
                    background: themeColors.alpha.card,
                    transition: "all 0.2s ease-in-out",
                    "&:hover": {
                      background: themeColors.alpha.hover,
                      boxShadow: `inset 3px 0 10px ${themeColors.glow}15`,
                    },
                    borderBottom:
                      index !== hunt_items.length - 1
                        ? `1px solid ${themeColors.alpha.card}`
                        : "none",
                  }}
                >
                  <Box
                    component="td"
                    sx={{
                      px: 3,
                      py: 2,
                      color: COMMON_COLORS.text.muted,
                      fontWeight: 600,
                    }}
                  >
                    {index + 1}
                  </Box>
                  <Box
                    component="td"
                    sx={{
                      px: 3,
                      py: 2,
                      color: COMMON_COLORS.text.tertiary,
                      fontWeight: 500,
                    }}
                  >
                    {item.name}
                  </Box>
                  <Box
                    component="td"
                    sx={{
                      px: 3,
                      py: 2,
                    }}
                  >
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      transition={{ type: "spring", stiffness: 400, damping: 17 }}
                      style={{ display: "inline-block" }}
                    >
                      <Chip
                        label={item.scheduled_time}
                        size="small"
                        icon={
                          isNeutralSchedule ? null : (
                            <AccessTimeIcon
                              sx={{
                                color: `${themeColors.primary.main} !important`,
                              }}
                            />
                          )
                        }
                        sx={{
                          background: isNeutralSchedule
                            ? "rgba(107, 114, 128, 0.2)"
                            : `${themeColors.primary.main}33`,
                          color: isNeutralSchedule
                            ? COMMON_COLORS.text.muted
                            : themeColors.primary.light,
                          fontWeight: 600,
                          border: `1px solid ${
                            isNeutralSchedule
                              ? "rgba(107, 114, 128, 0.3)"
                              : `${themeColors.primary.main}4D`
                          }`,
                        }}
                      />
                    </motion.div>
                  </Box>
                </Box>
              );
            })}
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}
