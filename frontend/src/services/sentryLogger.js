import * as Sentry from "@sentry/react";

function normalizeAttributeValue(value) {
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return value;
  }

  if (value instanceof Error) {
    return `${value.name}: ${value.message}`;
  }

  if (value === null) {
    return "null";
  }

  if (value === undefined) {
    return undefined;
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function normalizeAttributes(attributes = {}) {
  return Object.fromEntries(
    Object.entries(attributes)
      .map(([key, value]) => [key, normalizeAttributeValue(value)])
      .filter(([, value]) => value !== undefined),
  );
}

export function logInfo(message, attributes = {}) {
  if (!Sentry.isEnabled()) {
    return;
  }

  Sentry.logger.info(message, normalizeAttributes(attributes));
}

export function logWarn(message, attributes = {}) {
  if (!Sentry.isEnabled()) {
    return;
  }

  Sentry.logger.warn(message, normalizeAttributes(attributes));
}

export function logError(message, error, attributes = {}) {
  const normalizedAttributes = normalizeAttributes({
    ...attributes,
    errorName: error instanceof Error ? error.name : undefined,
    errorMessage: error instanceof Error ? error.message : String(error),
  });

  if (!Sentry.isEnabled()) {
    return;
  }

  Sentry.logger.error(message, normalizedAttributes);

  if (error instanceof Error) {
    Sentry.captureException(error, {
      level: "error",
      extra: normalizedAttributes,
    });
  }
}
