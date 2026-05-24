import { Box, Skeleton } from "@mui/material";
import { motion } from "framer-motion";
import { useThemeContext } from "../../../theme/ThemeContext";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
};

export default function SettingsSkeleton() {
  const { themeColors } = useThemeContext();

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants}>
      {/* Tab bar */}
      <Box
        component={motion.div}
        variants={itemVariants}
        sx={{
          display: "flex",
          justifyContent: "center",
          gap: 2,
          mb: 3,
        }}
      >
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} variant="rounded" width={70} height={36} />
        ))}
      </Box>

      {/* Section header */}
      <Box
        component={motion.div}
        variants={itemVariants}
        sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}
      >
        <Skeleton variant="rounded" width={32} height={32} sx={{ borderRadius: "8px" }} />
        <Skeleton variant="text" width={120} height={32} />
      </Box>

      {/* Form fields */}
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3, backdropFilter: "blur(8px)" }}>
        {[1, 2, 3, 4, 5].map((i) => (
          <Box
            key={i}
            component={motion.div}
            variants={itemVariants}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              p: 1,
              borderRadius: "8px",
              background: i % 2 === 0 ? themeColors.gradients.backgroundSubtle : "transparent",
            }}
          >
            <Skeleton variant="text" width="25%" height={28} />
            <Box sx={{ flex: 1 }}>
              <Skeleton variant="rounded" width="100%" height={40} />
            </Box>
          </Box>
        ))}
      </Box>
    </motion.div>
  );
}
