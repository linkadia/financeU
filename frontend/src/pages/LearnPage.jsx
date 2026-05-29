import { Stack, Typography } from "@mui/material";
import AppCard from "../components/AppCard";
import SectionHeader from "../components/SectionHeader";
import { courses } from "../mocks/courses";

export default function LearnPage() {
  return (
    <>
      <SectionHeader title="Learn" subtitle="Microlecciones financieras" />
      <Stack spacing={2}>
        {courses.map((course) => (
          <AppCard key={course.id}>
            <Typography variant="h6">{course.title}</Typography>
            <Typography color="text.secondary">{course.lessons} lecciones</Typography>
          </AppCard>
        ))}
      </Stack>
    </>
  );
}
