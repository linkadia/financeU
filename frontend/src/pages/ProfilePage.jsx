import { Typography } from "@mui/material";
import AppCard from "../components/AppCard";
import SectionHeader from "../components/SectionHeader";
import { useI18n } from "../i18n/I18nContext";

export default function ProfilePage() {
  const { t } = useI18n();

  return (
    <>
      <SectionHeader title={t("nav.profile")} subtitle={t("legacy.demoAccount")} />
      <AppCard>
        <Typography variant="h6">{t("legacy.demoUser")}</Typography>
        <Typography color="text.secondary">demo@finan3.app</Typography>
      </AppCard>
    </>
  );
}
