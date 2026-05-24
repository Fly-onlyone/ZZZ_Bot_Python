import { useState } from "react";
import { Box, Tab, Tabs } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import PersonIcon from "@mui/icons-material/Person";
import PasswordIcon from "@mui/icons-material/Password";
import CampaignIcon from "@mui/icons-material/Campaign";
import { ValueAdapter } from "../components";
import ManualLogin from "./ManualLogin";
import { BACKEND_URL } from "../config";
import { useThemeContext } from "../theme/ThemeContext";
import { getAuroraTabsStyles, auroraPanelVariants } from "../theme/tabStyles";

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
        sx={getAuroraTabsStyles(themeColors)}
      >
        <Tab label="Credentials" />
        <Tab label="Manual Browser" />
      </Tabs>

      <AnimatePresence mode="wait" initial={false} custom={tabDirection}>
        <Box
          key={activeTab}
          component={motion.div}
          custom={tabDirection}
          variants={auroraPanelVariants}
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
