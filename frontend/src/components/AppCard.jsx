import { Card } from "@mui/material";

export default function AppCard({ children, sx = {} }) {
  return (
    <Card sx={{ p: 2, bgcolor: "background.paper", border: "1px solid rgba(255,255,255,0.08)", ...sx }}>
      {children}
    </Card>
  );
}
