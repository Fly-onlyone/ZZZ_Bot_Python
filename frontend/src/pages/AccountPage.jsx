import React, { useState } from "react";
import { Box, Tab, Tabs } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import PersonIcon from "@mui/icons-material/Person";
import PasswordIcon from "@mui/icons-material/Password";
import CampaignIcon from "@mui/icons-material/Campaign";
import { ValueAdapter } from "../components";
import ManualLogin from "./ManualLogin";
import { BACKEND_URL } from "../config";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";

const panelVariants = {
  initial: (direction) => ({
    opacity: 0,
    x: direction * 20,
    scale: 0.995,
  }),
  animate: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 140,
      damping: 22,
      mass: 0.9,
    },
  },
  exit: (direction) => ({
    opacity: 0,
    x: direction * -20,
    scale: 0.995,
    transition: {
      duration: 0.18,
      ease: "easeInOut",
    },
  }),
};

export default function AccountPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [tabDirection, setTabDirection] = useState(1);
  const { themeColors } = useThemeContext();

  const handleTabChange = (_, newValue) => {
    setTabDirection(newValue >= activeTab ? 1 : -1);
    setActiveTab(newValue);
  };

  return (
    <Box>
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        centered
        sx={{
          mb: 3,
          minHeight: 48,
          "& .MuiTabs-indicator": { display: "none" },
          "& .MuiTab-root": {
            minHeight: 48,
            minWidth: "auto",
            px: 2.5,
            color: COMMON_COLORS.text.muted,
            fontWeight: 600,
            textTransform: "none",
            position: "relative",
            "&::after": {
              content: '""',
              position: "absolute",
              left: 12,
              right: 12,
              bottom: 0,
              height: 3,
              borderRadius: "999px",
              backgroundColor: "transparent",
              transition: "background-color 0.2s ease",
            },
            "&.Mui-selected": {
              color: themeColors.primary.light,
            },
            "&.Mui-selected::after": {
              backgroundColor: themeColors.primary.main,
            },
          },
        }}
      >
        <Tab label="Credentials" />
        <Tab label="Manual Browser" />
      </Tabs>

      <AnimatePresence mode="wait" initial={false} custom={tabDirection}>
        <Box
          key={activeTab}
          component={motion.div}
          custom={tabDirection}
          variants={panelVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          {activeTab === 0 && (
            <ValueAdapter
              customSections={{
                "HoYo Account": {
                  icon: (
                    <img
                      src={`${BACKEND_URL}/images/Hoyo.png`}
                      alt="HoYoLab"
                      style={{
                        width: "1.5rem",
                        height: "1.5rem",
                        borderRadius: "4px",
                      }}
                    />
                  ),
                  fields: ["hoyo_username", "hoyo_password"],
                },
                "Apprise Notification": {
                  icon: <CampaignIcon />,
                  fields: ["username", "app_password"],
                },
              }}
              customIcons={{
                hoyo_username: <PersonIcon />,
                hoyo_password: <PasswordIcon />,
                username: <PersonIcon />,
                app_password: <PasswordIcon />,
              }}
            />
          )}
          {activeTab === 1 && <ManualLogin />}
        </Box>
      </AnimatePresence>
    </Box>
  );
}
