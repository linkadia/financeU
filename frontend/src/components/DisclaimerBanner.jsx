import { Alert } from "@mui/material";

export default function DisclaimerBanner() {
  return (
    <Alert severity="warning" sx={{ mb: 2 }}>
      Contenido educativo e infotainment. No constituye asesoramiento financiero.
    </Alert>
  );
}
