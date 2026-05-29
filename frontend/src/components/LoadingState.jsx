import { Skeleton, Stack } from "@mui/material";

export default function LoadingState() {
  return (
    <Stack spacing={2}>
      <Skeleton variant="rounded" height={100} />
      <Skeleton variant="rounded" height={100} />
    </Stack>
  );
}
