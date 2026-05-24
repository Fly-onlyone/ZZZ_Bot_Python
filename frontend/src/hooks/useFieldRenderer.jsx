import { PASSWORD_FIELD_KEYWORDS } from "../config";
import { ArrayField, BooleanField, SelectField, TextField } from "../components";

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
    return PASSWORD_FIELD_KEYWORDS.some((keyword) => key.toLowerCase().includes(keyword));
  };

  /**
   * Renders the appropriate field component based on field type.
   *
   * Discrete controls (select, array, boolean) commit immediately after their
   * onChange fires. Text inputs defer the commit to onBlur — see TextField.
   *
   * @param {string} key - Field key/name
   * @param {*} value - Field value
   * @param {Function} onChange - Change handler
   * @param {Function} [onCommit] - Called when the edit should be persisted
   * @returns {JSX.Element} Field component
   */
  const renderField = (key, value, onChange, onCommit) => {
    const fieldConfig = typeConfig[key];
    const isPassword = isPasswordField(key);
    // Contract: `onChange` MUST synchronously write the new value to the source
    // of truth that `onCommit` reads (today: useFormState writes via
    // queryClient.setQueryData and commit() reads queryClient.getQueryData).
    // If onChange ever becomes async or batched, onCommit will fire against
    // stale state and silently save the previous value.
    const changeAndCommit = (next) => {
      onChange(next);
      onCommit?.();
    };

    // Custom select field
    if (fieldConfig?.type === "select" && fieldConfig?.options) {
      return (
        <SelectField
          id={key}
          value={value}
          options={fieldConfig.options}
          onChange={changeAndCommit}
        />
      );
    }

    // Array field (time pickers)
    if (Array.isArray(value)) {
      return <ArrayField value={value} onChange={changeAndCommit} />;
    }

    // Boolean field (switch)
    if (typeof value === "boolean") {
      return <BooleanField id={key} value={value} onChange={changeAndCommit} />;
    }

    // Text/Password field (default) — commits on blur, not on every keystroke.
    return (
      <TextField
        id={key}
        value={value}
        onChange={onChange}
        onCommit={onCommit}
        isPassword={isPassword}
      />
    );
  };

  return { renderField, isPasswordField };
}
