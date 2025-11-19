import React from "react";
import { PASSWORD_FIELD_KEYWORDS } from "../config";
import {
  ArrayField,
  BooleanField,
  SelectField,
  TextField,
} from "../components";

/**
 * useFieldRenderer Hook
 *
 * Provides field rendering logic based on field type and configuration.
 * Automatically detects field types and returns appropriate components.
 *
 * @param {Object} typeConfig - Custom type configuration for fields
 * @returns {Function} renderField function that renders appropriate field component
 */
export function useFieldRenderer(typeConfig = {}) {
  /**
   * Determines if a field is a password field based on keywords
   */
  const isPasswordField = (key) => {
    return PASSWORD_FIELD_KEYWORDS.some((keyword) =>
      key.toLowerCase().includes(keyword)
    );
  };

  /**
   * Renders the appropriate field component based on field type
   *
   * @param {string} key - Field key/name
   * @param {*} value - Field value
   * @param {Function} onChange - Change handler
   * @returns {JSX.Element} Field component
   */
  const renderField = (key, value, onChange) => {
    const fieldConfig = typeConfig[key];
    const isPassword = isPasswordField(key);

    // Custom select field
    if (fieldConfig?.type === "select" && fieldConfig?.options) {
      return (
        <SelectField
          id={key}
          value={value}
          options={fieldConfig.options}
          onChange={onChange}
        />
      );
    }

    // Array field (time pickers)
    if (Array.isArray(value)) {
      return <ArrayField value={value} onChange={onChange} />;
    }

    // Boolean field (switch)
    if (typeof value === "boolean") {
      return <BooleanField id={key} value={value} onChange={onChange} />;
    }

    // Text/Password field (default)
    return (
      <TextField
        id={key}
        value={value}
        onChange={onChange}
        isPassword={isPassword}
      />
    );
  };

  return { renderField, isPasswordField };
}
