import { Box, Button, CircularProgress, Stack, Typography } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { AnimatePresence, motion } from "framer-motion";
import { COMMON_COLORS } from "../../theme/colors";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * SaveStatus
 *
 * Small inline pill that surfaces the result of an auto-save. Driven by the
 * status string returned from useAutoSave. Renders nothing when idle so it
 * never adds visual noise on a clean page.
 */
export default function SaveStatus({ status, error, onRetry }) {
  const { themeColors } = useThemeContext();

  const pillBase = {
    display: "inline-flex",
    alignItems: "center",
    gap: 1,
    px: 1.5,
    py: 0.5,
    borderRadius: "999px",
    backdropFilter: "blur(8px)",
    fontSize: "0.8125rem",
    fontWeight: 500,
    letterSpacing: "0.02em",
  };

  const variants = {
    initial: { opacity: 0, y: -4 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -4 },
  };

  let content = null;

  if (status === "saving") {
    content = (
      <motion.div key="saving" variants={variants} initial="initial" animate="animate" exit="exit">
        <Box
          sx={{
            ...pillBase,
            background: `${themeColors.primary.main}1f`,
            border: `1px solid ${themeColors.primary.main}55`,
            color: themeColors.primary.light,
          }}
        >
          <CircularProgress size={12} thickness={5} sx={{ color: themeColors.primary.light }} />
          <Typography component="span" variant="caption" sx={{ fontWeight: 500 }}>
            Saving…
          </Typography>
        </Box>
      </motion.div>
    );
  } else if (status === "saved") {
    content = (
      <motion.div key="saved" variants={variants} initial="initial" animate="animate" exit="exit">
        <Box
          sx={{
            ...pillBase,
            background: `${COMMON_COLORS.success.main}1f`,
            border: `1px solid ${COMMON_COLORS.success.main}55`,
            color: COMMON_COLORS.success.light,
          }}
        >
          <CheckCircleIcon sx={{ fontSize: 14 }} />
          <Typography component="span" variant="caption" sx={{ fontWeight: 500 }}>
            Saved
          </Typography>
        </Box>
      </motion.div>
    );
  } else if (status === "error") {
    const message = error instanceof Error ? error.message : "Save failed";
    content = (
      <motion.div key="error" variants={variants} initial="initial" animate="animate" exit="exit">
        <Stack
          direction="row"
          spacing={1}
          alignItems="center"
          sx={{
            ...pillBase,
            background: `${COMMON_COLORS.error.main}1f`,
            border: `1px solid ${COMMON_COLORS.error.main}66`,
            color: COMMON_COLORS.error.light,
            pr: 0.5,
          }}
        >
          <ErrorOutlineIcon sx={{ fontSize: 14 }} />
          <Typography component="span" variant="caption" sx={{ fontWeight: 500 }} title={message}>
            Save failed
          </Typography>
          {onRetry && (
            <Button
              size="small"
              onClick={onRetry}
              sx={{
                minWidth: 0,
                px: 1,
                py: 0,
                fontSize: "0.75rem",
                fontWeight: 600,
                color: COMMON_COLORS.error.light,
                textTransform: "none",
                "&:hover": { background: `${COMMON_COLORS.error.main}22` },
              }}
            >
              Retry
            </Button>
          )}
        </Stack>
      </motion.div>
    );
  }

  return (
    <Box
      sx={{
        display: "inline-flex",
        alignItems: "center",
        minHeight: 28,
      }}
    >
      <AnimatePresence mode="wait">{content}</AnimatePresence>
    </Box>
  );
}
