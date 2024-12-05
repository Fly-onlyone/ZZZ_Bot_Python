import { useState } from "react";
import {
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
} from "@mui/material";
import InputIcon from "@mui/icons-material/Input";

export default function ManualLogin() {
  const [url, setUrl] = useState(""); // Initialize with a string for controlled Select
  const BACKEND_URL = "http://127.0.0.1:8000";
  const MINO_URL =
    "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?...";
  const REDEEM_URL = "https://zenless.hoyoverse.com/redemption";

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${BACKEND_URL}/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }), // Wrap url in an object
      });
      if (response.ok) {
        console.log("Success:", response.statusText);
      } else {
        console.log("Failed to fetch data:", response.statusText);
      }
    } catch (error) {
      console.error("Error occurred:", error);
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
        >
          <MenuItem value={MINO_URL}>MINO_URL</MenuItem>
          <MenuItem value={REDEEM_URL}>REDEEM_URL</MenuItem>
        </Select>
      </FormControl>
      <IconButton onClick={handleSubmit}>
        <InputIcon />
      </IconButton>
    </div>
  );
}
