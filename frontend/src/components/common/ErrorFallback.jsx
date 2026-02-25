import { Box, Button, Typography } from "@mui/material";
import { IconAlertTriangle } from "@tabler/icons-react";

/**
 * Error boundary fallback UI for Sentry ErrorBoundary.
 *
 * @param {Object} props
 * @param {Error} props.error - The caught error
 * @param {function} props.resetError - Call to reset the error boundary
 */
export default function ErrorFallback({ error, resetError }) {
  return (
    <Box
      alignItems="center"
      display="flex"
      flexDirection="column"
      gap={2}
      justifyContent="center"
      minHeight="100vh"
      p={4}
      textAlign="center"
    >
      <IconAlertTriangle color="error" size={48} />
      <Typography variant="h5">Something went wrong</Typography>
      <Typography color="text.secondary" variant="body2">
        {error?.message || "An unexpected error occurred."}
      </Typography>
      <Button onClick={resetError} variant="outlined">
        Try again
      </Button>
    </Box>
  );
}
