import React, { useEffect, useState } from "react";
import { TimePicker } from "@mui/x-date-pickers";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { Alert, Snackbar, Switch, TextField } from "@mui/material";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs from "dayjs";
import SaveIcon from "@mui/icons-material/Save";

export default function Setting() {
  const [settings, setSettings] = useState({});
  const [alert, setAlert] = useState({ open: false, type: "success", message: "" });
  const BACKEND_URL = "http://127.0.0.1:8000";


  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/settings`);
        if (response.ok) {
          const data = await response.json();
          setSettings(data); // Dynamically populate state
        } else {
          console.error("Failed to fetch settings:", response.statusText);
        }
      } catch (error) {
        console.error("Error fetching settings:", error);
      }
    };
    fetchSettings();
  }, []);

  // Handle dynamic state changes
  const handleChange = (key, value) => {
    setSettings((prev) => ({
      ...prev, [key]: value
    }));
  };

// Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${BACKEND_URL}/settings`, {
        method: "POST", headers: {
          "Content-Type": "application/json"
        }, body: JSON.stringify(settings)
      });

      if (response.ok) {
        setAlert({ open: true, type: "success", message: "Settings saved successfully!" });
      } else {
        setAlert({ open: true, type: "error", message: "Error saving settings." });
      }
    } catch (error) {
      console.error("Error saving settings:", error);
      setAlert({ open: true, type: "error", message: "Error saving settings." });
    }
  };

  // Handle closing the alert
  const handleCloseAlert = () => {
    setAlert({ ...alert, open: false });
  };
  // Render dynamic fields based on `settings` keys
  const renderFields = () => {
    return Object.keys(settings).map((key) => {
      const value = settings[key];

      // Render TimePicker for time-based settings
      if (Array.isArray(value)) {
        return (<div key={key} className="mb-6">
          <label
            className="block text-lg font-medium mb-2 capitalize">{key.replace(/_/g, " ")}:</label>
          <div className="space-y-4">
            {value.map((time, index) => (<div
              key={index}
              className="flex items-center justify-between gap-4 bg-gray-700 p-3 rounded-lg"
            >
              <TimePicker
                label="Select Time"
                value={time ? dayjs(time, "HH:mm") : null}
                onChange={(newValue) => {
                  const updatedArray = [...value];
                  updatedArray[index] = newValue ? newValue.format("HH:mm") : "";
                  handleChange(key, updatedArray);
                }}
              />
              <button
                type="button"
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg"
                onClick={() => {
                  const updatedArray = value.filter((_, i) => i !== index);
                  handleChange(key, updatedArray);
                }}
              >
                Remove
              </button>
            </div>))}
            <button
              type="button"
              className="mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg"
              onClick={() => handleChange(key, [...value, ""])}
            >
              Add Time
            </button>
          </div>
        </div>);
      }

      // Render Checkbox for boolean values
      if (typeof value === "boolean") {
        return (<div key={key} className="flex items-center justify-between mb-6">
          <label htmlFor={key} className="font-medium text-lg capitalize text-teal-300">
            {key.replace(/_/g, " ")}
          </label>
          <Switch
            id={key}
            name={key}
            checked={value}
            onChange={(e) => handleChange(key, e.target.checked)}
            color="primary"
          />
        </div>);
      }
      // Render Text Input for other types of values
      return (<div key={key} className="mb-6">
        <label htmlFor={key} className="block text-lg font-medium mb-2 capitalize">
          {key.replace(/_/g, " ")}:
        </label>
        <TextField
          id={key}
          value={value}
          onChange={(e) => handleChange(key, e.target.value)}
          fullWidth
          variant="outlined"
          size="small"
          sx={{
            bgcolor: "white", borderRadius: "5px"
          }}
        />
      </div>);
    });
  };

  return (<LocalizationProvider dateAdapter={AdapterDayjs}>
    <div className="mx-auto p-8 bg-gray-800 rounded-lg shadow-lg ">
      <form onSubmit={handleSubmit} className="space-y-6">
        {renderFields()}
        <button
          type="submit"
          className="flex items-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg w-full text-lg"
        >
          <SaveIcon />
          Save Settings
        </button>
        {/* Snackbar for Alerts */}
        <Snackbar
          open={alert.open}
          autoHideDuration={3000}
          onClose={handleCloseAlert}
          anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        >
          <Alert onClose={handleCloseAlert} severity={alert.type} variant="outlined">
            {alert.message}
          </Alert>
        </Snackbar>
      </form>
    </div>
  </LocalizationProvider>);
}