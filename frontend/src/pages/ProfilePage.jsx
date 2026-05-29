import { Typography } from "@mui/material";
import AppCard from "../components/AppCard";
import SectionHeader from "../components/SectionHeader";

export default function ProfilePage() {
  return (
    <>
      <SectionHeader title="Perfil" subtitle="Cuenta demo" />
      <AppCard>
        <Typography variant="h6">Usuario demo</Typography>
        <Typography color="text.secondary">demo@finan3.app</Typography>
      </AppCard>
    </>
  );
}
