import { AppBar, Box, Toolbar, Typography } from "@mui/material";
import LanguageSwitcher from "./LanguageSwitcher";

export default function TopBar() {
  return (
    <AppBar position="sticky" elevation={0} sx={{ bgcolor: "background.default" }}>
      <Toolbar sx={{ justifyContent: "space-between" }}>
        <Typography variant="h6" color="primary" fontWeight={800}>
          FINAN3
        </Typography>
        <Box sx={{ color: "text.primary" }}>
          <LanguageSwitcher compact />
        </Box>
      </Toolbar>
    </AppBar>
  );
}
