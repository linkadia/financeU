import { AppBar, Toolbar, Typography } from "@mui/material";

export default function TopBar() {
  return (
    <AppBar position="sticky" elevation={0} sx={{ bgcolor: "background.default" }}>
      <Toolbar>
        <Typography variant="h6" color="primary" fontWeight={800}>
          FINAN3
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
