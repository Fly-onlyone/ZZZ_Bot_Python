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
        sx={{
          display: "flex",
          gap: 3,
          mb: 3,
          flexWrap: "wrap",
        }}
      >
        <Chip
          label={`Day: ${day}`}
          sx={{
            background: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
            color: "#ffffff",
            fontWeight: 600,
            fontSize: "16px",
            padding: "24px 12px",
            borderRadius: "10px",
            boxShadow: "0 4px 14px rgba(139, 92, 246, 0.3)",
          }}
        />
        <Chip
          label={check_in}
          icon={
            check_in === "Login Success" ? (
              <CheckCircleIcon sx={{ color: "#ffffff !important" }} />
            ) : (
              <ErrorIcon sx={{ color: "#ffffff !important" }} />
            )
          }
          sx={{
            background:
              check_in === "Login Success"
                ? "linear-gradient(135deg, #10b981 0%, #059669 100%)"
                : "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
            color: "#ffffff",
            fontWeight: 600,
            fontSize: "16px",
            padding: "24px 12px",
            borderRadius: "10px",
            boxShadow:
              check_in === "Login Success"
                ? "0 4px 14px rgba(16, 185, 129, 0.3)"
                : "0 4px 14px rgba(239, 68, 68, 0.3)",
          }}
        />
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
