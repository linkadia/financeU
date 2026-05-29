import { Typography } from "@mui/material";
import AppCard from "../components/AppCard";
import SectionHeader from "../components/SectionHeader";
import MarketTicker from "../components/MarketTicker";
import DisclaimerBanner from "../components/DisclaimerBanner";
import { useI18n } from "../i18n/I18nContext";

export default function HomePage() {
  const { t } = useI18n();

  return (
    <>
      <MarketTicker />
      <DisclaimerBanner />
      <SectionHeader title={t("nav.home")} subtitle={t("legacy.homeSubtitle")} />
      <AppCard>
        <Typography variant="h6">{t("legacy.analysis")}</Typography>
        <Typography variant="body2" color="text.secondary">
          {t("legacy.weeklySummary")}
        </Typography>
      </AppCard>
    </>
  );
}
