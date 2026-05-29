import { Alert } from "@mui/material";
import { useI18n } from "../i18n/I18nContext";

export default function DisclaimerBanner() {
  const { t } = useI18n();

  return (
    <Alert severity="warning" sx={{ mb: 2 }}>
      {t('legacy.disclaimer')}
    </Alert>
  );
}
