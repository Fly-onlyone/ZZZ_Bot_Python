import React, { useState } from "react";
import { TimePicker } from "@mui/x-date-pickers";
import { Divider, IconButton, Switch, TextField } from "@mui/material";
import dayjs from "dayjs";
import { useLocation } from "react-router-dom";
import { ContentCopy, Visibility, VisibilityOff } from "@mui/icons-material";
import { useQueryClient } from "@tanstack/react-query";
import { DataLoader } from "./DataLoader";
import SaveButton from "./SaveButton";

export default function ValueAdapter({
  customIcons = {},
  customSections = null,
}) {
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });
  const [passwordVisibility, setPasswordVisibility] = useState({});
  const location = useLocation();
  const route = location.pathname.replace("/", "");

  const { useRouteData, useSaveData } = DataLoader();

  const { data: value = {}, error } = useRouteData(route);
  const mutation = useSaveData(route);

  const queryClient = useQueryClient();

  const handleChange = (key, newValue) => {
    queryClient.setQueryData([route], (prev) => ({
      ...prev,
      [key]: newValue,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(value, {
      onSuccess: () => {
        setAlert({
          open: true,
          type: "success",
          message: "Data saved successfully!",
        });
      },
      onError: () => {
        setAlert({
          open: true,
          type: "error",
          message: "Failed to save data.",
        });
      },
    });
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
        <div className="space-y-4">
          {fieldValue.map((time, index) => (
            <div
              key={index}
              className="flex items-center justify-between gap-4 rounded-lg bg-gray-700 p-3"
            >
              <TimePicker
                label="Select Time"
                value={time ? dayjs(time, "HH:mm") : null}
                onChange={(newValue) => {
                  const updatedArray = [...fieldValue];
                  updatedArray[index] = newValue
                    ? newValue.format("HH:mm")
                    : "";
                  handleChange(key, updatedArray);
                }}
              />
              <button
                type="button"
                className="h-12 w-1/12 rounded-lg bg-red-600 px-4 py-2 text-lg font-medium text-white hover:bg-red-700"
                onClick={() => {
                  const updatedArray = fieldValue.filter((_, i) => i !== index);
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
            onClick={() => handleChange(key, [...fieldValue, ""])}
          >
            Add Time
          </button>
        </div>
      );
    } else if (typeof fieldValue === "boolean") {
      return (
        <Switch
          id={key}
          checked={fieldValue}
          onChange={(e) => handleChange(key, e.target.checked)}
          color="primary"
          className="ml-auto"
        />
      );
    } else if (isPassword) {
      return (
        <div className="flex flex-grow items-center gap-2">
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
            onClick={() => navigator.clipboard.writeText(fieldValue || "")}
            title="Copy to clipboard"
          >
            <ContentCopy />
          </IconButton>
        </div>
      );
    } else {
      return (
        <div className="flex flex-grow items-center gap-2">
          <TextField
            className="pr-12"
            id={key}
            value={fieldValue || ""}
            onChange={(e) => handleChange(key, e.target.value)}
            fullWidth
          />
          <IconButton
            onClick={() => navigator.clipboard.writeText(fieldValue || "")}
            title="Copy to clipboard"
          >
            <ContentCopy />
          </IconButton>
        </div>
      );
    }
  };

  const renderSection = (sectionKey, sectionData, index, length) => {
    if (!sectionKey || !sectionData || !sectionData.fields?.length) return null;

    const { fields, icon } = sectionData;

    return (
      <div key={sectionKey} className="mb-8">
        <div className="mb-4 flex items-center gap-4">
          {icon && <div className="text-2xl">{icon}</div>}
          <h2 className="text-2xl font-semibold capitalize">
            {sectionKey.replace(/_/g, " ")}
          </h2>
        </div>
        <div className="space-y-6">
          {fields.map((fieldKey) => (
            <div
              key={fieldKey}
              className={`${
                !Array.isArray(value[fieldKey]) ? "flex items-center gap-4" : ""
              }`}
            >
              <label
                className={`flex gap-4 text-lg font-medium capitalize ${
                  !Array.isArray(value[fieldKey]) ? "w-1/4" : "mb-4"
                }`}
              >
                {customIcons[fieldKey] && (
                  <div className="flex items-center">
                    {customIcons[fieldKey]}
                  </div>
                )}
                {fieldKey.replace(/_/g, " ")}:
              </label>
              <div
                className={`${
                  !Array.isArray(value[fieldKey]) ? "flex w-3/4" : ""
                }`}
              >
                {renderField(fieldKey)}
              </div>
            </div>
          ))}
        </div>
        {index + 1 < length && <Divider className="mt-6" />}
      </div>
    );
  };

  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="mb-10">
        {customSections
          ? Object.keys(customSections).map((sectionKey, index) =>
              renderSection(
                sectionKey,
                customSections[sectionKey],
                index,
                Object.keys(customSections).length
              )
            )
          : Object.keys(value).map((key) => (
              <div
                key={key}
                className={`mb-6 ${
                  !Array.isArray(value[key]) ? "flex items-center gap-4" : ""
                }`}
              >
                <label
                  className={`flex gap-4 text-lg font-medium capitalize ${
                    !Array.isArray(value[key]) ? "w-1/4" : "mb-4"
                  }`}
                >
                  {customIcons[key] && (
                    <div className="flex items-center">{customIcons[key]}</div>
                  )}
                  {key.replace(/_/g, " ")}:
                </label>
                <div
                  className={`${
                    !Array.isArray(value[key]) ? "flex w-3/4" : ""
                  } `}
                >
                  {renderField(key)}
                </div>
              </div>
            ))}
      </div>
      <SaveButton onSave={handleSubmit} alert={alert} setAlert={setAlert} />
    </form>
  );
}
