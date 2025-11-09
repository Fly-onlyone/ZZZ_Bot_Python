import React from "react";
import { Alert, Button, Snackbar } from "@mui/material";
import SaveIcon from "@mui/icons-material/Save";
import { buttonStyles } from "./theme/styles";

const SaveButton = ({ onSave, alert, setAlert }) => {
  const handleCloseAlert = () => {
    setAlert({ ...alert, open: false });
  };

  return (
    <>
      <Button
        variant="contained"
        onClick={onSave}
        startIcon={<SaveIcon />}
        sx={{
          mt: 2,
          px: 3,
          py: 1.5,
          ...buttonStyles.primary,
        }}
      >
        Save
      </Button>

      <Snackbar
        open={alert.open}
        autoHideDuration={3000}
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={alert.type} variant="outlined">
          {alert.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default SaveButton;
