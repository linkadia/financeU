# Learning module

## Future REST endpoints proposal

- `GET /api/learning/categories/`: active categories with levels and course counts.
- `GET /api/learning/course-types/`: active course types.
- `GET /api/learning/levels/`: active levels.
- `GET /api/learning/courses/`: list active courses, filterable by `category`, `course_type`, `level`.
- `GET /api/learning/courses/{slug}/`: course detail with ordered active lessons and user progress.
- `GET /api/learning/courses/{slug}/progress/`: current user's course progress.
- `GET /api/learning/lessons/{slug}/`: lesson detail with quiz options.
- `POST /api/learning/lessons/{id}/start/`: create or update `UserLessonProgress` as in progress.
- `POST /api/learning/lessons/{id}/quiz/answer/`: submit an option, complete the lesson only if correct, then recalculate course progress.
- `GET /api/learning/progress/`: global Learning progress for the current user.

## Initial data

Load the sample catalog with:

```bash
python manage.py loaddata initial_learning_data
```
