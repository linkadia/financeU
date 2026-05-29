import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: "#0A0F1E",
      paper: "#111827",
    },
    primary: {
      main: "#F5A623",
    },
    text: {
      primary: "#FFFFFF",
      secondary: "#AAB2C0",
    },
  },
  shape: {
    borderRadius: 16,
  },
  typography: {
    fontFamily: ["Inter", "Roboto", "Arial", "sans-serif"].join(","),
  },
});

export default theme;
