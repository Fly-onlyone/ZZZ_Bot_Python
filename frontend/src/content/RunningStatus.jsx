import { BACKEND_URL, DataLoader } from "../services/DataLoader";
import { Alert, Typography } from "@mui/material";
import ScheduleIcon from "@mui/icons-material/Schedule";
import { EmptyState, RunningStatusSkeleton } from "../components";
import { motion } from "framer-motion";
import React from "react";
import { DateTimeField } from "@mui/x-date-pickers";
import dayjs from "dayjs";
import { useThemeContext } from "../theme/ThemeContext";

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

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: {
    opacity: 1,
    y: 0,
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

export default function RunningStatus() {
  const { useRouteData } = DataLoader();
  const { themeColors } = useThemeContext();
  const { data, error } = useRouteData("check-run-status");

  if (error) {
    return (
      <Alert severity="error">
        Failed to fetch mission data: {error.message}
      </Alert>
    );
  }
  if (!data) {
    return <RunningStatusSkeleton />;
  }

  const { last_run, next_run } = data;

  if (!last_run && !next_run) {
    return (
      <EmptyState
        icon={<ScheduleIcon />}
        title="No Run History"
        subtitle="The bot hasn't run yet. Schedule a run or start one manually."
      />
    );
  }

  return (
    <motion.div
      className="space-x-8 pt-6"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <motion.div
        className="flex flex-row items-center justify-center gap-6"
        variants={containerVariants}
      >
        <motion.img
          src={`${BACKEND_URL}/images/Zhu Yuan02.ico`}
          variants={iconVariants}
          whileHover={{ scale: 1.1, rotate: 5 }}
          transition={{ type: "spring", stiffness: 400, damping: 17 }}
        />
        <motion.div variants={itemVariants}>
          <Typography
            className="mb-2 font-semibold"
            variant="h6"
            sx={{ color: themeColors.primary.main }}
          >
            Last run
          </Typography>
        </motion.div>
        <motion.div variants={itemVariants}>
          <DateTimeField
            defaultValue={dayjs(last_run, "HH:mm DD/MM/YY")}
            format={"DD/MM/YYYY - hh:mm A"}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <Typography
            className="mb-2 font-semibold"
            variant="h6"
            sx={{ color: themeColors.secondary.main }}
          >
            Next run
          </Typography>
        </motion.div>
        <motion.div variants={itemVariants}>
          <DateTimeField
            defaultValue={dayjs(next_run, "HH:mm DD/MM/YY")}
            format={"DD/MM/YYYY - hh:mm A"}
          />
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
