import { Box } from "@mui/material";
import { Outlet } from "react-router-dom";
import TopBar from "../components/TopBar";
import BottomNav from "../components/BottomNav";

export default function MainLayout() {
  return (
    <Box sx={{ minHeight: "100vh", pb: 8 }}>
      <TopBar />
      <Box component="main" sx={{ p: 2, maxWidth: 480, mx: "auto" }}>
        <Outlet />
      </Box>
      <BottomNav />
    </Box>
  );
}
