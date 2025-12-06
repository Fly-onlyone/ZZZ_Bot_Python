import { useState } from "react";
import {
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";

export default function ManualLogin() {
  const BACKEND_URL = "http://127.0.0.1:8000";
  const MINO_URL =
    "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?...";
  const REDEEM_URL = "https://zenless.hoyoverse.com/redemption";

  const [url, setUrl] = useState(MINO_URL); // Default to MINO_URL
  const [playState, setPlayState] = useState(false);

  const handleIconClick = (e) => {
    e.preventDefault();
    const newPlayState = !playState; // Compute the new state
    setPlayState(newPlayState); // Update the state
    handleSubmit(newPlayState); // Pass the new state directly
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
        console.log("Success:", response.statusText);

        // Periodically check the backend playState
        if (updatedPlayState) {
          const intervalId = setInterval(async () => {
            try {
              const stateResponse = await fetch(`${BACKEND_URL}/playstate`);
              const { playState: backendPlayState } =
                await stateResponse.json();
              if (!backendPlayState) {
                setPlayState(false); // Update the frontend playState
                clearInterval(intervalId); // Stop checking
                console.log("Browser session ended");
              }
            } catch (error) {
              console.error("Error checking playState:", error);
              setPlayState(false);
              clearInterval(intervalId);
            }
          }, 500); // Check every 500ms for faster response
        }
      } else {
        console.error("Failed to fetch data:", response.statusText);
      }
    } catch (error) {
      console.error("Error occurred:", error);
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
          labelId="demo-simple-select-label"
          id="demo-simple-select"
          value={url}
          label="Url"
          onChange={handleChange}
          disabled={playState} // Disable dropdown when playState is true
        >
          <MenuItem value={MINO_URL}>MINO_URL</MenuItem>
          <MenuItem value={REDEEM_URL}>REDEEM_URL</MenuItem>
        </Select>
      </FormControl>
      <IconButton onClick={handleIconClick}>
        {playState ? <StopIcon /> : <PlayArrowIcon />}
      </IconButton>
    </div>
  );
}
