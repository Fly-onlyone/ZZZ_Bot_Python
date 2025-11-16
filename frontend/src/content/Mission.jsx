import React from "react";
import { Alert, Box, Chip, Paper, Typography } from "@mui/material";
import { BACKEND_URL, DataLoader } from "../DataLoader";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";

export default function Mission() {
  const { useRouteData } = DataLoader();

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
    return <Typography>Loading...</Typography>; // Display loading state
  }
  const { day, check_in, missions } = mission;
  if (!missions) {
    return <Alert severity="error">Today task hasn't done yet</Alert>;
  }

  return (
    <div>
      <Box
        sx={{ mb: 3, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}
      >
        <Paper
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background:
              "linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%)",
            border: "1px solid rgba(139, 92, 246, 0.3)",
            textAlign: "center",
          }}
        >
          <Typography
            variant="body2"
            sx={{ color: "#94a3b8", fontWeight: 600, mb: 1, display: "block" }}
          >
            Current Day
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 700, color: "#a78bfa" }}>
            {day}
          </Typography>
        </Paper>
        <Paper
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background:
              check_in === "Login Success"
                ? "linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)"
                : "linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%)",
            border: `1px solid ${
              check_in === "Login Success"
                ? "rgba(16, 185, 129, 0.3)"
                : "rgba(239, 68, 68, 0.3)"
            }`,
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1,
          }}
        >
          {check_in === "Login Success" ? (
            <CheckCircleIcon sx={{ color: "#10b981", fontSize: 32 }} />
          ) : (
            <ErrorIcon sx={{ color: "#ef4444", fontSize: 32 }} />
          )}
          <Typography
            variant="body1"
            sx={{
              fontWeight: 600,
              color: check_in === "Login Success" ? "#34d399" : "#f87171",
            }}
          >
            {check_in}
          </Typography>
        </Paper>
      </Box>

      {check_in === "Login Success" && (
        <Box
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
              border: "1px solid rgba(16, 185, 129, 0.2)",
              boxShadow: "0 4px 20px rgba(16, 185, 129, 0.15)",
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

      <Typography
        variant="h6"
        sx={{
          mb: 2,
          fontWeight: 600,
          color: "#cbd5e1",
        }}
      >
        Mission Status
      </Typography>
      <Box
        sx={{
          borderRadius: "12px",
          overflow: "hidden",
          border: "1px solid rgba(139, 92, 246, 0.2)",
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
              background:
                "linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%)",
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
                  color: "#e2e8f0",
                  borderBottom: "1px solid rgba(139, 92, 246, 0.2)",
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
                  color: "#e2e8f0",
                  borderBottom: "1px solid rgba(139, 92, 246, 0.2)",
                }}
              >
                Status
              </Box>
            </Box>
          </Box>
          <Box component="tbody">
            {missions.map((mission, index) => (
              <Box
                component="tr"
                key={index}
                sx={{
                  background:
                    mission.state === "Finished"
                      ? "rgba(16, 185, 129, 0.08)"
                      : "rgba(239, 68, 68, 0.08)",
                  transition: "all 0.2s ease-in-out",
                  "&:hover": {
                    background:
                      mission.state === "Finished"
                        ? "rgba(16, 185, 129, 0.15)"
                        : "rgba(239, 68, 68, 0.15)",
                  },
                  borderBottom:
                    index !== missions.length - 1
                      ? "1px solid rgba(139, 92, 246, 0.1)"
                      : "none",
                }}
              >
                <Box
                  component="td"
                  sx={{
                    px: 3,
                    py: 2,
                    color: "#cbd5e1",
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
                        <CheckCircleIcon sx={{ color: "#10b981 !important" }} />
                      ) : (
                        <ErrorIcon sx={{ color: "#ef4444 !important" }} />
                      )
                    }
                    sx={{
                      background:
                        mission.state === "Finished"
                          ? "rgba(16, 185, 129, 0.2)"
                          : "rgba(239, 68, 68, 0.2)",
                      color:
                        mission.state === "Finished" ? "#34d399" : "#f87171",
                      fontWeight: 600,
                      border: `1px solid ${
                        mission.state === "Finished"
                          ? "rgba(16, 185, 129, 0.3)"
                          : "rgba(239, 68, 68, 0.3)"
                      }`,
                    }}
                  />
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </div>
  );
}
