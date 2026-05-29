import { Stack, Typography } from "@mui/material";
import AppCard from "../components/AppCard";
import SectionHeader from "../components/SectionHeader";
import { marketAssets } from "../mocks/assets";
import { useI18n } from "../i18n/I18nContext";

export default function MarketsPage() {
  const { t } = useI18n();

  return (
    <>
      <SectionHeader title={t("nav.markets")} subtitle={t("legacy.mainAssets")} />
      <Stack spacing={2}>
        {marketAssets.map((asset) => (
          <AppCard key={asset.symbol}>
            <Typography variant="h6">{asset.name}</Typography>
            <Typography color="text.secondary">
              {asset.symbol} - {asset.price}
            </Typography>
          </AppCard>
        ))}
      </Stack>
    </>
  );
}
