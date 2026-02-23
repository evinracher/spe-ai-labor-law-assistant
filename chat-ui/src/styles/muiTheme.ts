import { createTheme } from "@mui/material";
import { COLORS } from "./colors";

// ─── MUI THEME ───────────────────────────────────────────────────────────────
export const theme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: COLORS.darkBg,
      paper: COLORS.darkSurface,
    },
    primary: {
      main: COLORS.gold,
      contrastText: "#111111",
    },
    text: {
      primary: COLORS.textOnDarkPrimary,
      secondary: COLORS.textOnDarkSecondary,
    },
    divider: COLORS.dividerOnDark,
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 15,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        "html, body, #root": {
          height: "100%",
          margin: 0,
          padding: 0,
          backgroundColor: COLORS.darkBg,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: COLORS.darkBg,
          backgroundImage: "none",
          borderBottom: `1px solid ${COLORS.dividerOnDark}`,
          boxShadow: "none",
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            backgroundColor: "rgba(255,255,255,0.05)",
            color: COLORS.textOnDarkPrimary,
            borderRadius: 12,
            "& fieldset": {
              borderColor: "rgba(255,255,255,0.15)",
            },
            "&:hover fieldset": {
              borderColor: "rgba(212,175,55,0.5)",
            },
            "&.Mui-focused fieldset": {
              borderColor: COLORS.gold,
              borderWidth: 1.5,
            },
          },
          "& .MuiInputBase-input::placeholder": {
            color: COLORS.textOnDarkSecondary,
            opacity: 1,
          },
        },
      },
    },
  },
});
