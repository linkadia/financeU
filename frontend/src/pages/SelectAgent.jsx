import { useI18n } from "../i18n/I18nContext";

export default function SelectAgent() {
  const { t } = useI18n();

  return (
    <div>
      <h1>{t("profile.aiCompanion")}</h1>
    </div>
  );
}
