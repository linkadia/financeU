import { Typography } from "@mui/material";
import AppCard from "../components/AppCard";
import SectionHeader from "../components/SectionHeader";
import MarketTicker from "../components/MarketTicker";
import DisclaimerBanner from "../components/DisclaimerBanner";

export default function HomePage() {
  return (
    <>
      <MarketTicker />
      <DisclaimerBanner />
      <SectionHeader title="Inicio" subtitle="Tu resumen financiero educativo de hoy" />
      <AppCard>
        <Typography variant="h6">Análisis semanal</Typography>
        <Typography variant="body2" color="text.secondary">
          Resumen de tendencias crypto y forex para aprendizaje.
        </Typography>
      </AppCard>
    </>
  );
}
