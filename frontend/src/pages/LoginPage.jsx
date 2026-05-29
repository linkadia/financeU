import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const { t } = useI18n();

  return (
    <Box sx={{ minHeight: "100vh", p: 3, display: "grid", placeItems: "center" }}>
      <Box sx={{ width: "100%", maxWidth: 420 }}>
        <Typography variant="h3" color="primary" fontWeight={900}>FINAN3</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 1, mb: 3 }}>
          {t("legacy.mobilePitch")}
        </Typography>
        <Button fullWidth variant="contained" onClick={() => navigate("/")}>
          {t("legacy.demoLogin")}
        </Button>
      </Box>
    </Box>
  );
}
