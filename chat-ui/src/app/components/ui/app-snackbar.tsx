import { Snackbar, Alert } from "@mui/material";
import { COLORS } from "../../../styles/colors";

interface AppSnackbarProps {
  open: boolean;
  message: string;
  severity: "success" | "error";
  onClose: () => void;
}

export default function AppSnackbar({
  open,
  message,
  severity,
  onClose,
}: AppSnackbarProps) {
  return (
    <Snackbar
      open={open}
      autoHideDuration={3500}
      onClose={onClose}
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
    >
      <Alert
        onClose={onClose}
        severity={severity}
        variant="filled"
        sx={{
          borderRadius: "10px",
          fontSize: "0.875rem",
          backgroundColor:
            severity === "error" ? "#B00020" : COLORS.darkSurface,
          color: "#FFFFFF",
          border:
            severity === "success"
              ? `1px solid ${COLORS.dividerOnDark}`
              : "none",
          "& .MuiAlert-icon": {
            color: severity === "error" ? "#FFB3B3" : COLORS.gold,
          },
        }}
      >
        {message}
      </Alert>
    </Snackbar>
  );
}
