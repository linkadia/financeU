import { BottomNavigation, BottomNavigationAction, Paper } from "@mui/material";
import HomeIcon from "@mui/icons-material/Home";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import SchoolIcon from "@mui/icons-material/School";
import PersonIcon from "@mui/icons-material/Person";
import { useLocation, useNavigate } from "react-router-dom";

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Paper sx={{ position: "fixed", bottom: 0, left: 0, right: 0 }} elevation={8}>
      <BottomNavigation value={location.pathname} onChange={(_, value) => navigate(value)}>
        <BottomNavigationAction label="Home" value="/" icon={<HomeIcon />} />
        <BottomNavigationAction label="Markets" value="/markets" icon={<ShowChartIcon />} />
        <BottomNavigationAction label="Learn" value="/learn" icon={<SchoolIcon />} />
        <BottomNavigationAction label="Profile" value="/profile" icon={<PersonIcon />} />
      </BottomNavigation>
    </Paper>
  );
}
