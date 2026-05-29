import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const navigate = useNavigate();

  return (
    <Box sx={{ minHeight: "100vh", p: 3, display: "grid", placeItems: "center" }}>
      <Box sx={{ width: "100%", maxWidth: 420 }}>
        <Typography variant="h3" color="primary" fontWeight={900}>FINAN3</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 1, mb: 3 }}>
          Crypto & Finance 24/7 on your mobile.
        </Typography>
        <Button fullWidth variant="contained" onClick={() => navigate("/")}>
          Entrar demo
        </Button>
      </Box>
    </Box>
  );
}
