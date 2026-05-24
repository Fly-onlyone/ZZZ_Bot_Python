import { useState, useRef } from "react";
import { FormControl, IconButton, InputLabel, MenuItem, Select } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import * as Sentry from "@sentry/react";
import { BACKEND_URL } from "../config";
import { logError, logInfo, logWarn } from "../services/sentryLogger.js";
import { useThemeContext } from "../theme/ThemeContext";
import { GLOW } from "../theme/styles";

export default function ManualLogin() {
  const MINO_URL = "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?...";
  const REDEEM_URL = "https://zenless.hoyoverse.com/redemption";
  const CHECK_IN_URL =
    "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091&hyl_auth_required=true";

  const [url, setUrl] = useState(MINO_URL); // Default to MINO_URL
  const [playState, setPlayState] = useState(false);
  const spanFinishRef = useRef(null);
  const { themeColors } = useThemeContext();

  const handleIconClick = (e) => {
    e.preventDefault();
    const newPlayState = !playState; // Compute the new state
    logInfo("Manual login toggle requested", {
      nextPlayState: newPlayState,
      url,
    });
    setPlayState(newPlayState); // Update the state
    void handleSubmit(newPlayState); // Pass the new state directly
  };

  const handleSubmit = async (updatedPlayState) => {
    try {
      const payload = { url, playState: updatedPlayState };
      const response = await fetch(`${BACKEND_URL}/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        logInfo("Manual login request accepted", {
          playState: updatedPlayState,
          status: response.status,
          statusText: response.statusText,
          url,
        });

        // Periodically check the backend playState
        if (updatedPlayState) {
          Sentry.startSpan({ op: "ui.manual_login", name: "manual-login-polling" }, (span) => {
            spanFinishRef.current = () => span.end();
            const intervalId = setInterval(async () => {
              try {
                const stateResponse = await fetch(`${BACKEND_URL}/playstate`);
                const { playState: backendPlayState } = await stateResponse.json();
                if (!backendPlayState) {
                  setPlayState(false);
                  clearInterval(intervalId);
                  spanFinishRef.current?.();
                  spanFinishRef.current = null;
                  logInfo("Manual browser session ended", {
                    url,
                  });
                }
              } catch (error) {
                logError("Manual login polling failed", error, {
                  url,
                });
                setPlayState(false);
                clearInterval(intervalId);
                spanFinishRef.current?.();
                spanFinishRef.current = null;
              }
            }, 500);
          });
        }
      } else {
        logWarn("Manual login request rejected", {
          playState: updatedPlayState,
          status: response.status,
          statusText: response.statusText,
          url,
        });
      }
    } catch (error) {
      logError("Manual login request failed", error, {
        playState: updatedPlayState,
        url,
      });
      setPlayState(false); // Reset playState on frontend in case of fetch error
    }
  };

  const handleChange = (e) => {
    setUrl(e.target.value);
  };

  return (
    <div className="flex flex-grow items-center gap-2">
      <FormControl fullWidth>
        <InputLabel id="demo-simple-select-label">Url</InputLabel>
        <Select
          variant="outlined"
          labelId="demo-simple-select-label"
          id="demo-simple-select"
          value={url}
          label="Url"
          onChange={handleChange}
          disabled={playState} // Disable dropdown when playState is true
        >
          <MenuItem value={MINO_URL}>MINO_URL</MenuItem>
          <MenuItem value={REDEEM_URL}>REDEEM_URL</MenuItem>
          <MenuItem value={CHECK_IN_URL}>CHECK_IN_URL</MenuItem>
        </Select>
      </FormControl>
      <IconButton
        onClick={handleIconClick}
        sx={{
          transition: "all 0.3s ease-in-out",
          "&:hover": {
            boxShadow: playState ? GLOW.subtle("#ef4444") : GLOW.subtle(themeColors.glow),
          },
        }}
      >
        {playState ? <StopIcon /> : <PlayArrowIcon />}
      </IconButton>
    </div>
  );
}
