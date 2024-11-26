import React, { useEffect, useState } from "react";
import { TimePicker } from "@mui/x-date-pickers";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { Alert, IconButton, Snackbar, Switch, TextField } from "@mui/material";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs from "dayjs";
import { useLocation } from "react-router-dom";
import { ContentCopy, Visibility, VisibilityOff } from "@mui/icons-material";

export default function ValueAdapter() {
  const [value, setValue] = useState({});
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [passwordVisibility, setPasswordVisibility] = useState({});
  const BACKEND_URL = "http://127.0.0.1:8000";
  const location = useLocation();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const route = location.pathname.replace("/", "");
        const response = await fetch(`${BACKEND_URL}/${route}`);
        if (response.ok) {
          const data = await response.json();
          setValue(data);
          setPasswordVisibility(
            Object.keys(data).reduce((acc, key) => {
              acc[key] = key.toLowerCase().includes("password") ? false : null;
              return acc;
            }, {})
          );
        } else {
          setError(`Failed to fetch data: ${response.statusText}`);
        }
      } catch (err) {
        setError("An error occurred while fetching data.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [location.pathname]);

  const handleChange = (key, value) =>
    setValue((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const route = location.pathname.replace("/", "");
      const response = await fetch(`${BACKEND_URL}/${route}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(value),
      });
      const pageName =
        String(route).charAt(0).toUpperCase() + String(route).slice(1);

      if (response.ok) {
        setAlert({
          open: true,
          type: "success",
          message: `${pageName} saved successfully!`,
        });
      } else {
        setAlert({
          open: true,
          type: "error",
          message: `Failed to save ${pageName}.`,
        });
      }
    } catch {
      setAlert({ open: true, type: "error", message: "Error saving data." });
    }
  };
  const togglePasswordVisibility = (key) => {
    setPasswordVisibility((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const renderField = (key) => {
    const fieldValue = value[key];
    const isPassword = key.toLowerCase().includes("password");
    if (Array.isArray(fieldValue)) {
      return (
        <div key={key} className="mb-6">
          <div className="space-y-4">
            {fieldValue.map((time, index) => (
              <div
                key={index}
                className="flex items-center justify-between gap-4 rounded-lg bg-gray-700 p-3"
              >
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <TimePicker
                    label="Select Time"
                    value={time ? dayjs(time, "HH:mm") : null}
                    onChange={(newValue) => {
                      const updatedArray = [...value];
                      updatedArray[index] = newValue
                        ? newValue.format("HH:mm")
                        : "";
                      handleChange(key, updatedArray);
                    }}
                  />
                </LocalizationProvider>
                <button
                  type="button"
                  className="h-12 w-1/12 rounded-lg bg-red-600 px-4 py-2 text-lg font-medium text-white hover:bg-red-700"
                  onClick={() => {
                    const updatedArray = value.filter((_, i) => i !== index);
                    handleChange(key, updatedArray);
                  }}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              className="mt-4 h-12 w-1/12 rounded-lg bg-green-600 px-4 py-2 text-lg font-medium text-white hover:bg-green-900"
              onClick={() => handleChange(key, [...value, ""])}
            >
              Add Time
            </button>
          </div>
        </div>
      );
    } else if (typeof fieldValue === "boolean") {
      return (
        <Switch
          id={key}
          checked={fieldValue}
          onChange={(e) => handleChange(key, e.target.checked)}
          color="primary"
        />
      );
    } else if (isPassword) {
      return (
        <div key={key} className="mb-6">
          <div className="flex items-center gap-2">
            <TextField
              id={key}
              type={passwordVisibility[key] ? "text" : "password"}
              value={fieldValue || ""}
              onChange={(e) => handleChange(key, e.target.value)}
              fullWidth
            />
            <IconButton
              onClick={() => togglePasswordVisibility(key)}
              title={passwordVisibility[key] ? "Hide" : "Show"}
            >
              {passwordVisibility[key] ? <VisibilityOff /> : <Visibility />}
            </IconButton>
            <IconButton
              onClick={() => navigator.clipboard.writeText(fieldValue)}
              title="Copy to clipboard"
            >
              <ContentCopy />
            </IconButton>
          </div>
        </div>
      );
    } else {
      return (
        <div key={key} className="mb-6">
          <div className="flex items-center gap-2">
            <TextField
              id={key}
              value={fieldValue}
              onChange={(e) => handleChange(key, e.target.value)}
              fullWidth
            />
            <IconButton
              onClick={() => navigator.clipboard.writeText(fieldValue)}
              title="Copy to clipboard"
            >
              <ContentCopy />
            </IconButton>
          </div>
        </div>
      );
    }
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {Object.keys(value).map((key) => (
        <div key={key} className="mb-6">
          <label className="block text-lg font-medium capitalize">
            {key.replace(/_/g, " ")}:
          </label>
          {renderField(key)}
        </div>
      ))}
      <button
        type="submit"
        className="h-12 w-2/12 rounded-lg bg-blue-600 px-5 py-2 text-xl text-white hover:bg-blue-900"
      >
        Save
      </button>
      <Snackbar
        open={alert.open}
        autoHideDuration={3000}
        onClose={() => setAlert({ ...alert, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={alert.type} variant="outlined">
          {alert.message}
        </Alert>
      </Snackbar>
    </form>
  );
}
