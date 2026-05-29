import React from "react";
import ReactDOM from "react-dom/client";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { OnboardingProvider } from "./context/OnboardingContext";
import { I18nProvider } from "./i18n/I18nContext";
import theme from "./theme/theme";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <I18nProvider>
          <OnboardingProvider>
            <App />
          </OnboardingProvider>
        </I18nProvider>
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);
