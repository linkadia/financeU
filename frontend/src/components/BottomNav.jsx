import { BottomNavigation, BottomNavigationAction, Paper } from "@mui/material";
import HomeIcon from "@mui/icons-material/Home";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import SchoolIcon from "@mui/icons-material/School";
import PersonIcon from "@mui/icons-material/Person";
import { useLocation, useNavigate } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useI18n();

  return (
    <Paper sx={{ position: "fixed", bottom: 0, left: 0, right: 0 }} elevation={8}>
      <BottomNavigation value={location.pathname} onChange={(_, value) => navigate(value)}>
        <BottomNavigationAction label={t('nav.home')} value="/" icon={<HomeIcon />} />
        <BottomNavigationAction label={t('nav.markets')} value="/markets" icon={<ShowChartIcon />} />
        <BottomNavigationAction label={t('nav.learn')} value="/learn" icon={<SchoolIcon />} />
        <BottomNavigationAction label={t('nav.profile')} value="/profile" icon={<PersonIcon />} />
      </BottomNavigation>
    </Paper>
  );
}
