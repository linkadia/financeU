import { Stack, Typography } from "@mui/material";
import AppCard from "../components/AppCard";
import SectionHeader from "../components/SectionHeader";
import { marketAssets } from "../mocks/assets";

export default function MarketsPage() {
  return (
    <>
      <SectionHeader title="Markets" subtitle="Activos principales" />
      <Stack spacing={2}>
        {marketAssets.map((asset) => (
          <AppCard key={asset.symbol}>
            <Typography variant="h6">{asset.name}</Typography>
            <Typography color="text.secondary">{asset.symbol} — {asset.price}</Typography>
          </AppCard>
        ))}
      </Stack>
    </>
  );
}
