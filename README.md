# FinanU

FinanU es una aplicación mobile-first de educación financiera con onboarding personalizado, companion AI, feed de mercado, microcursos con quizzes y perfil de usuario. La app está pensada como una experiencia de aprendizaje guiada: primero identifica intereses, tolerancia al riesgo, objetivo financiero y estilo de acompañamiento; después muestra contenido y cursos adaptados a ese contexto.

El idioma principal de la aplicación es polaco. También incluye inglés y un selector de idioma persistente para que el usuario cambie entre `PL` y `EN`.

## Estado Actual

- Frontend funcional en React + Vite.
- Backend Django REST con endpoints para usuarios, onboarding, ajustes, contenido, mercados y suscripciones.
- Catálogo Learning avanzado modelado en backend, con fixtures iniciales y lógica de progreso, pendiente de exponer como API pública.
- La pantalla principal de aprendizaje del frontend usa datos locales traducidos y guarda progreso en `localStorage`.
- Autenticación simplificada con `UserProfile`, contraseña hasheada y sesión guardada en navegador.

## Funcionalidad de Producto

### Autenticación

- Registro con usuario, email, contraseña y confirmación.
- Login con usuario o email.
- Redirección automática según estado de onboarding:
  - usuario nuevo: onboarding;
  - usuario con onboarding completo: dashboard.
- Persistencia de usuario actual en el navegador.

### Onboarding

El onboarding tiene cuatro pasos:

1. Selección de companion AI:
   - `Finn`: mentor para fundamentos y aprendizaje progresivo.
   - `Nova`: estratega para análisis más avanzado.
2. Selección de intereses:
   - Crypto.
   - Stock Market.
   - Forex.
   - Investing Basics.
3. Perfil de riesgo:
   - Low.
   - Medium.
   - High.
4. Objetivo financiero:
   - Emergency Fund.
   - Crypto/Stocks.
   - Major Purchase.
   - Retirement.

Al finalizar, el frontend llama al backend para marcar el onboarding como completado y guardar las preferencias.

### Dashboard

- Feed mobile con filtros por categoría.
- Artículo destacado de la semana.
- Tarjetas de noticias/alertas de mercado.
- Microcurso del día.
- Acceso inferior a navegación principal.

### Learning

- Catálogo de cursos con filtros por tema, nivel y formato.
- Cursos con vídeo embebido de YouTube.
- Lecciones con resumen, duración y quiz.
- Progreso global y por curso.
- Una lección se completa solo al responder correctamente su quiz.
- El progreso actual del frontend se guarda localmente en `localStorage`.

### Perfil y Ajustes

- Edición de usuario y email.
- Edición de preferencias de onboarding:
  - intereses;
  - perfil de riesgo;
  - objetivo principal;
  - companion AI.
- Cambio de contraseña solicitando contraseña actual.
- Cierre de sesión.

### Multiidioma

- Idioma principal: polaco.
- Idioma secundario: inglés.
- Selector visible en login, signup, onboarding y cabeceras internas.
- Persistencia del idioma en `localStorage`.
- Traducciones centralizadas en `frontend/src/i18n/translations.js`.
- Datos localizados para dashboard y cursos en:
  - `frontend/src/data/localizedDashboard.js`;
  - `frontend/src/data/localizedCourses.js`.

## Arquitectura

```text
finanU/
  backend/
    finan3_backend/      Configuración Django y urls raíz
    users/               Perfiles, login, onboarding y settings
    content/             Artículos, cursos simples y lecciones simples
    markets/             Activos y señales
    subscriptions/       Suscripciones
    learning/            Modelo avanzado de cursos, quizzes y progreso
  frontend/
    src/
      api/               Cliente API
      components/        Componentes UI y layout
      context/           Contextos de app
      data/              Datos localizados/mock
      i18n/              Provider y traducciones
      pages/             Pantallas principales
      utils/             Gestión de sesión
```

## Stack Técnico

### Frontend

- React.
- Vite.
- React Router.
- Material UI para rutas legacy y algunos componentes base.
- Tailwind-style utility classes ya presentes en las pantallas Stitch.
- i18n propio sin dependencia externa.
- Persistencia local:
  - `finanu.language`: idioma seleccionado.
  - sesión de usuario en utilidades de `frontend/src/utils/session.js`.
  - `finan3_learning_progress`: progreso de aprendizaje.

### Backend

- Django.
- Django REST Framework.
- django-cors-headers.
- python-dotenv.
- SQLite en desarrollo.
- MySQL preparado para produccion mediante variables de entorno.
- Gunicorn + Docker preparados para hosting.

## Instalación

### Requisitos

- Python 3.12 recomendado.
- Node.js y npm.
- Windows PowerShell, terminal integrada o shell compatible.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver 8001
```

API local:

```text
http://127.0.0.1:8001/api/
```

Para exponer en red local:

```bash
python manage.py runserver 0.0.0.0:8001
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

App local:

```text
http://127.0.0.1:5173/
```

En PowerShell, si `npm` falla por política de ejecución, usa:

```bash
npm.cmd run dev
npm.cmd run build
```

Para probar desde móvil en la misma Wi-Fi:

```bash
npm run dev -- --host 0.0.0.0
```

Ajusta estas variables a tu IP local:

- `frontend/.env`: `VITE_API_BASE_URL`.
- `backend/.env`: `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.

## Variables de Entorno

### `backend/.env`

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_SECURE_SSL_REDIRECT=False
DB_ENGINE=sqlite
SQLITE_NAME=db.sqlite3
```

### `frontend/.env`

```env
VITE_API_BASE_URL=http://127.0.0.1:8001/api
```

## Preparacion para Despliegue

El desarrollo local sigue usando SQLite por defecto. No hace falta Docker para probar en tu PC:

```bash
cd backend
python manage.py runserver 8001

cd frontend
npm run dev
```

Cuando tengamos hosting en AWS, la configuracion preparada permite mover el backend a MySQL/RDS cambiando variables de entorno, sin tocar codigo.

### Variables de produccion del backend

Ejemplo para `backend/.env.production` o para variables configuradas directamente en el servicio de AWS:

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_ALLOWED_HOSTS=api.tudominio.com,tudominio.com
CORS_ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com
CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_SECURE_SSL_REDIRECT=False

DB_ENGINE=mysql
DB_NAME=finanu
DB_USER=finanu_user
DB_PASSWORD=replace-with-real-password
DB_HOST=replace-with-rds-endpoint.amazonaws.com
DB_PORT=3306
DB_CONN_MAX_AGE=60
```

No subir `backend/.env.production` al repositorio. Las credenciales reales deben vivir en variables del hosting, AWS Secrets Manager, Parameter Store o un fichero `.env` local no versionado.

### Backend con Docker

El backend incluye:

- `backend/Dockerfile`: imagen de produccion con Django, Gunicorn, MySQL client y collectstatic.
- `backend/requirements-prod.txt`: dependencias extra para produccion.
- `docker-compose.production.example.yml`: ejemplo para levantar el contenedor con un `.env.production`.

Construir imagen:

```bash
docker build -t finanu-backend ./backend
```

Ejecutar localmente una imagen de produccion usando variables:

```bash
docker run --env-file backend/.env.production -p 8001:8001 finanu-backend
```

Con Docker Compose:

```bash
docker compose -f docker-compose.production.example.yml up --build
```

Antes de servir trafico en produccion, ejecutar migraciones contra MySQL/RDS:

```bash
docker compose -f docker-compose.production.example.yml run --rm backend python manage.py migrate
```

Crear superusuario si hace falta:

```bash
docker compose -f docker-compose.production.example.yml run --rm backend python manage.py createsuperuser
```

### Frontend en produccion

El frontend de Vite se puede desplegar como archivos estaticos:

```bash
cd frontend
npm install
npm run build
```

La carpeta `frontend/dist/` se puede publicar en S3 + CloudFront, Amplify, Netlify, Vercel o un Nginx. En produccion, `frontend/.env.production` deberia apuntar al dominio real de la API:

```env
VITE_API_BASE_URL=https://api.tudominio.com/api
```

### Migrar datos de SQLite a MySQL

Cuando la base MySQL/RDS este creada:

1. Mantener una copia de seguridad de `backend/db.sqlite3`.
2. Exportar los datos actuales desde SQLite:

```bash
cd backend
python manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission > data.json
```

3. Cambiar variables de entorno a MySQL (`DB_ENGINE=mysql`, `DB_HOST`, `DB_NAME`, etc.).
4. Crear tablas en MySQL:

```bash
python manage.py migrate
```

5. Importar los datos:

```bash
python manage.py loaddata data.json
```

6. Probar login, registro, onboarding y vistas principales antes de apuntar el dominio publico.

Si aparecen conflictos de claves o datos duplicados, se vacia la base MySQL nueva y se repite la importacion. No borrar la SQLite original hasta confirmar que todo funciona.

## Scripts Útiles

Frontend:

```bash
npm run dev
npm run build
npm run preview
```

Backend:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8001
python manage.py loaddata initial_learning_data
```

## API Backend

Base URL:

```text
/api/
```

### Usuarios

```text
POST   /api/users/login/
GET    /api/users/profiles/
POST   /api/users/profiles/
GET    /api/users/profiles/{id}/
PATCH  /api/users/profiles/{id}/
POST   /api/users/profiles/{id}/complete-onboarding/
GET    /api/users/profiles/{id}/settings/
PATCH  /api/users/profiles/{id}/settings/
```

Login acepta:

```json
{
  "identifier": "username-or-email",
  "password": "password"
}
```

Completar onboarding acepta:

```json
{
  "interests": ["crypto", "forex"],
  "risk_profile": "medium",
  "goal": "investing",
  "selected_agent": "finn"
}
```

### Content

```text
GET/POST/PATCH/DELETE /api/content/articles/
GET/POST/PATCH/DELETE /api/content/courses/
GET/POST/PATCH/DELETE /api/content/lessons/
```

### Markets

```text
GET/POST/PATCH/DELETE /api/markets/assets/
GET/POST/PATCH/DELETE /api/markets/signals/
```

### Subscriptions

```text
GET/POST/PATCH/DELETE /api/subscriptions/
```

### Learning

El módulo `learning` contiene modelos completos para catálogo, lecciones, quizzes y progreso. Actualmente no está enlazado en `finan3_backend/urls.py`, por lo que no expone endpoints REST públicos todavía.

Modelos principales:

- `LearningCategory`.
- `CourseType`.
- `LearningLevel`.
- `Course`.
- `Lesson`.
- `LessonQuiz`.
- `LessonQuizOption`.
- `UserLessonProgress`.
- `UserCourseProgress`.

El fixture inicial se carga con:

```bash
python manage.py loaddata initial_learning_data
```

## Guía de Usuario

1. Abre la app en el navegador.
2. Elige idioma desde el selector `PL`/`EN`.
3. Crea una cuenta o inicia sesión.
4. Si es tu primera vez, completa el onboarding:
   - elige companion AI;
   - marca tus intereses;
   - selecciona tu perfil de riesgo;
   - define tu objetivo financiero.
5. Entra al dashboard para ver feed, alertas y microcurso.
6. En `Nauka`/`Learn`, filtra cursos y abre una lección.
7. Mira el vídeo, lee el resumen y responde el quiz.
8. Revisa tu progreso global y por curso.
9. En perfil puedes cambiar preferencias, contraseña o cerrar sesión.

## Conceptos Funcionales

- Companion AI: guía conceptual que personaliza el tono y tipo de aprendizaje.
- Perfil de riesgo: preferencia de volatilidad usada para personalización.
- Objetivo financiero: meta principal del usuario para priorizar contenido.
- Microcurso: unidad corta de aprendizaje accionable.
- Quiz obligatorio: mecanismo de validación para desbloquear progreso.
- Feed de mercado: contenido educativo de mercado, no asesoramiento financiero.

## Conceptos Técnicos

- `I18nProvider`: contexto React que expone `language`, `setLanguage`, `languages` y `t`.
- `LanguageSwitcher`: selector reutilizable para cambiar idioma.
- `OnboardingProvider`: mantiene el borrador del onboarding durante el flujo.
- `session.js`: encapsula lectura/escritura de usuario actual.
- `api/users.js`: cliente HTTP para login, registro, onboarding y settings.
- ViewSets DRF: CRUD estándar para recursos de contenido, mercados y suscripciones.
- Password hashing: las contraseñas se guardan hasheadas con utilidades de Django.
- CORS: configurado por variables de entorno para desarrollo local y red local.

## Limitaciones Conocidas

- La autenticación es simple y no usa JWT ni sesiones server-side.
- Learning en backend está modelado, pero el frontend actual usa datos locales traducidos.
- Las noticias y cursos visibles en frontend son contenido mock/localizado.
- Algunos módulos backend exponen CRUD abierto porque DRF está configurado con `AllowAny`.
- No hay suite de tests automatizados todavía.

## Verificación

Frontend:

```bash
cd frontend
npm.cmd run build
```

Backend:

```bash
cd backend
python manage.py check
python manage.py migrate
```

## Roadmap Sugerido

- Conectar el módulo `learning` del backend al frontend.
- Añadir autenticación real con tokens.
- Añadir permisos por usuario en settings, progreso y suscripciones.
- Migrar contenido mock a endpoints REST.
- Añadir tests unitarios e integración.
- Internacionalizar respuestas de error del backend.
- Añadir panel admin editorial para noticias, cursos y quizzes.
