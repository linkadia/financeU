import { Stack, Typography } from "@mui/material";
import AppCard from "../components/AppCard";
import SectionHeader from "../components/SectionHeader";
import { getCourses } from "../data/localizedCourses";
import { useI18n } from "../i18n/I18nContext";

export default function LearnPage() {
  const { language, t } = useI18n();
  const courses = getCourses(language);

  return (
    <>
      <SectionHeader title={t("nav.learn")} subtitle={t("legacy.financialMicroLessons")} />
      <Stack spacing={2}>
        {courses.map((course) => (
          <AppCard key={course.id}>
            <Typography variant="h6">{course.title}</Typography>
            <Typography color="text.secondary">
              {course.lessons.length} {t("legacy.lessons")}
            </Typography>
          </AppCard>
        ))}
      </Stack>
    </>
  );
}
