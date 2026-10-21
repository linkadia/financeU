# FinancU

FinancU es una aplicación mobile-first de educación financiera con onboarding personalizado, companion AI, feed de mercado, microcursos con quizzes y perfil de usuario. La app está pensada como una experiencia de aprendizaje guiada: primero identifica intereses, tolerancia al riesgo, objetivo financiero y estilo de acompañamiento; después muestra contenido y cursos adaptados a ese contexto.

El idioma principal de la aplicación es polaco. También incluye inglés y un selector de idioma persistente para que el usuario cambie entre `PL` y `EN`.

## Documentacion Funcional

### Estado Actual

- Frontend funcional en React + Vite.
- Backend Django REST con endpoints para usuarios, onboarding, ajustes, noticias, catalogo Learning, progreso y datos de mercado.
- Modelo de datos backend consolidado en `users`, `content`, `learning` y `marketdata`.
- Los modelos legacy vacios `content.Article`, `content.Course`, `content.Lesson`, `markets.MarketAsset`, `markets.Signal` y `subscriptions.Subscription` han sido eliminados mediante migraciones.
- La app `content` conserva solo `NewsArticle`, usado por el feed de noticias y el importador RSS.
- La pantalla principal de aprendizaje consume el catalogo `learning` del backend y puede caer a datos locales traducidos como fallback.
- El progreso de aprendizaje se sincroniza con backend cuando hay usuario y se conserva localmente como respaldo de UX.
- Autenticación simplificada con `UserProfile`, contraseña hasheada, recuperacion por contraseña temporal y sesión guardada en navegador.
- Los endpoints sensibles de usuarios tienen throttling basico por scope/IP.

### Funcionalidad de Producto

### Autenticación

- Registro con usuario, email, contraseña y confirmación.
- Login con usuario o email.
- Recuperacion de contraseña mediante generacion de contraseña temporal:
  - en desarrollo se devuelve en la respuesta para facilitar pruebas;
  - en produccion se envia por email y no se expone en la respuesta.
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

### Carrusel de Mercado

El dashboard incluye un carrusel con datos recientes de mercado. Su objetivo no es dar recomendaciones de inversión, sino ofrecer una lectura rápida y educativa del contexto financiero: crypto, índices, divisas, materias primas, tipos de interés y algunos indicadores macro.

El carrusel se alimenta desde el módulo `marketdata`. Cada activo o indicador tiene una ficha fija en la base de datos, por ejemplo `BTC`, `ETH`, `SP500`, `EURUSD`, `PL_CPI` o `ECB_RATE`. Lo que se actualiza periódicamente son sus valores:

- valor actual;
- valor anterior comparable;
- fecha o periodo del dato;
- fuente usada;
- variación calculada por el backend.

Para mantener estos datos frescos existe el comando:

```bash
python manage.py refresh_market_data_llm
```

El comando pide a Gemini que busque datos recientes en fuentes financieras y oficiales, usando Google Search grounding, y exige que la respuesta tenga un formato JSON compacto. Después el backend valida ese JSON y lo importa como snapshots de mercado. El frontend consume los últimos snapshots disponibles para mostrar el carrusel.

Flujo funcional:

1. El comando se ejecuta de forma programada, normalmente una vez al día.
2. Gemini consulta fuentes fiables y devuelve un JSON con los símbolos esperados.
3. Django valida que el JSON tenga las columnas correctas y que las filas sean importables.
4. El servicio de importación guarda o actualiza snapshots por producto.
5. El backend calcula variación absoluta, porcentaje y estado visual.
6. El dashboard muestra los últimos datos disponibles.

Si una fila viene incompleta, por ejemplo sin valor actual o sin fecha efectiva, el comando lo muestra en consola antes de importar. Esas filas pueden quedar como parciales o ser rechazadas por el servicio, según el tipo de problema. Esto permite revisar rápidamente si el modelo no encontró una fuente fiable para algún dato.

### Noticias RSS de Última Hora

FinancU también puede importar noticias financieras recientes desde varios RSS públicos. Este proceso sirve para alimentar el contenido educativo y de actualidad que verá el usuario en el feed.

El script responsable es:

```bash
python scripts/import_rss_news.py --llm
```

Qué hace funcionalmente:

1. Descarga noticias desde RSS financieros configurados en el script.
2. Une esas fuentes en un XML temporal.
3. Descarta noticias antiguas, duplicadas o ya importadas.
4. Para cada noticia nueva, Gemini interpreta el contenido.
5. Genera textos preparados para la app en inglés y polaco.
6. Clasifica la noticia por tipo, dificultad, importancia, etiquetas y activos mencionados.
7. Guarda la noticia como `NewsArticle` en el backend.

El script usa deduplicación para evitar publicar la misma noticia varias veces. Si el LLM falla en una noticia concreta, usa una clasificación heurística básica para no bloquear todo el proceso.

Por defecto solo importa noticias publicadas en las últimas 24 horas. Se puede sustituir esa ventana por una fecha mínima absoluta con:

```bash
python scripts/import_rss_news.py --llm --min-published-at 2026-06-01
```

Opciones útiles:

- `--llm`: activa interpretación con Gemini.
- `--limit 20`: procesa solo un número máximo de items RSS.
- `--from-existing-xml`: reutiliza un XML ya descargado.
- `--keep-xml`: no borra el XML temporal al terminar.
- `--xml path/to/rss_output.xml`: define dónde guardar o leer el XML temporal.

Igual que el carrusel de mercado, este proceso no da asesoramiento financiero. Resume y traduce noticias para aprendizaje y contexto.

### Learning

- Catálogo de cursos con filtros por tema, nivel y formato.
- Cursos con vídeo embebido de YouTube.
- Lecciones con resumen, duración y quiz.
- Progreso global, por curso y por lección.
- Bloqueo secuencial de cursos y lecciones para guiar la ruta de aprendizaje.
- Una lección se completa solo al responder correctamente su quiz.
- Si hay usuario autenticado, el progreso se consulta en `/api/learning/progress/` y se actualiza en `/api/learning/lessons/{lesson_id}/submit/`.
- `localStorage` conserva `finanu_learning_progress` como fallback y para mantener una experiencia fluida si la API no responde.

### Perfil y Ajustes

- Edición de usuario y email.
- Edición de preferencias de onboarding:
  - intereses;
  - perfil de riesgo;
  - objetivo principal;
  - companion AI.
- Cambio de contraseña solicitando contraseña actual.
- Recuperacion de acceso desde login mediante email.
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

## Documentacion Tecnica

## Arquitectura

```text
finanU/
  backend/
    finanu_backend/      Configuración Django y urls raíz
    users/               Perfiles, login, onboarding y settings
    content/             Noticias financieras interpretadas (`NewsArticle`)
    learning/            Catalogo, cursos, lecciones, quizzes y progreso
    marketdata/          Productos financieros, snapshots y runs de actualizacion
    markets/             App legacy sin modelos; conserva migraciones de borrado
    subscriptions/       App legacy sin modelos; conserva migraciones de borrado
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

## Modelo de Datos Backend

El modelo definitivo del backend queda centrado en cuatro dominios activos:

- `users.UserProfile`: identidad de usuario, login simplificado, estado de acceso, fecha de renovacion, preferencias de onboarding y companion seleccionado.
- `content.NewsArticle`: noticias importadas desde RSS, resumidas y clasificadas para el feed educativo. Incluye traducciones, dificultad, tipo de noticia, importancia, fuentes, tags, activos mencionados y estado editorial.
- `learning`: catalogo educativo completo. Incluye `LearningCategory`, `CourseType`, `LearningLevel`, `Course`, `Lesson`, `LessonQuiz`, `LessonQuizQuestion`, `LessonQuizOption`, `UserLessonProgress` y `UserCourseProgress`.
- `marketdata`: datos del carrusel de mercado. Incluye `FinancialProduct`, `FinancialProductSnapshot` y `FinancialDataRun`.

Modelos legacy eliminados:

- `content.Article`
- `content.Course`
- `content.Lesson`
- `markets.MarketAsset`
- `markets.Signal`
- `subscriptions.Subscription`

Las apps `markets` y `subscriptions` quedan sin modelos ni endpoints. Se mantienen registradas temporalmente para que sus migraciones de borrado puedan ejecutarse en todos los entornos. Cuando produccion y staging hayan aplicado esas migraciones, se pueden retirar por completo de `INSTALLED_APPS` y del repositorio.

## Stack Técnico

### Frontend

- React.
- Vite.
- React Router.
- Material UI para rutas legacy y algunos componentes base.
- Tailwind-style utility classes ya presentes en las pantallas Stitch.
- i18n propio sin dependencia externa.
- Cliente API con timeout y fallback automatico para peticiones `GET`/`HEAD`.
- Persistencia local:
  - `finanu.language`: idioma seleccionado.
  - sesión de usuario en utilidades de `frontend/src/utils/session.js`.
  - `finanu_learning_progress`: progreso de aprendizaje como respaldo local.

### Backend

- Django.
- Django REST Framework.
- django-cors-headers.
- python-dotenv.
- SQLite en desarrollo.
- MySQL preparado para produccion mediante variables de entorno.
- Cache local en desarrollo y Redis opcional en produccion para compartir throttling entre workers.
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
INTEGRATOR_WEBHOOK_SECRET=replace-with-shared-secret
MSISDN_HMAC_KEY=replace-with-a-long-independent-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_SECURE_SSL_REDIRECT=False
DB_ENGINE=sqlite
SQLITE_NAME=db.sqlite3
REDIS_URL=
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@finanu.local
```

Para actualizar el carrusel de mercado con Gemini y Google Search grounding:

```env
GOOGLE_API_KEY=replace-with-google-api-key
MARKET_LLM_MODEL=gemini-3.5-flash
MARKET_LLM_INPUT_USD_PER_1M=0
MARKET_LLM_OUTPUT_USD_PER_1M=0
MARKET_LLM_GOOGLE_SEARCH_USED_THIS_MONTH=0
```

Notas:

- `GOOGLE_API_KEY` o `GEMINI_API_KEY` es obligatorio para `refresh_market_data_llm`.
- `MARKET_LLM_MODEL` permite cambiar el modelo sin tocar código.
- `MARKET_LLM_INPUT_USD_PER_1M` y `MARKET_LLM_OUTPUT_USD_PER_1M` se usan solo para estimar coste por tokens. Por defecto son `0` para no presentar precios hardcodeados como verdad de facturación.
- `MARKET_LLM_GOOGLE_SEARCH_USED_THIS_MONTH` sirve para estimar el coste de Google Search grounding cuando se supera el tramo gratuito mensual. Es una ayuda operativa, no una fuente oficial de billing.

Para importar e interpretar noticias RSS:

```env
NEWS_LLM_MODEL=gemini-3.1-flash-lite
NEWS_MIN_PUBLISHED_AT=2026-06-01
```

Notas:

- El script RSS usa la misma `GOOGLE_API_KEY` cuando se ejecuta con `--llm`.
- `NEWS_LLM_MODEL` permite elegir el modelo usado para traducir y clasificar noticias.
- `NEWS_MIN_PUBLISHED_AT` es opcional. Si no se configura, el script usa una ventana móvil de las últimas 24 horas.

### `frontend/.env`

```env
VITE_API_BASE_URL=http://127.0.0.1:8001/api
VITE_API_FALLBACK_BASE_URLS=http://127.0.0.1:8000/api,http://localhost:8001/api,http://localhost:8000/api
VITE_API_TIMEOUT_MS=5000
```

## Proximos pasos para servidor, hosting y despliegue

### Preparacion para Despliegue

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
INTEGRATOR_WEBHOOK_SECRET=replace-with-shared-secret
MSISDN_HMAC_KEY=replace-with-a-long-independent-secret
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
REDIS_URL=redis://replace-with-redis-endpoint:6379/1
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=replace-with-smtp-host
EMAIL_PORT=587
EMAIL_HOST_USER=replace-with-smtp-user
EMAIL_HOST_PASSWORD=replace-with-smtp-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=no-reply@tudominio.com
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
docker compose -f docker-compose.production.example.yml up --build -d
```

Al iniciar el contenedor, `docker-entrypoint.sh` ejecuta `python manage.py migrate --noinput` con las variables de `backend/.env.production`. Gunicorn arranca solo si las migraciones terminan correctamente. En un reinicio posterior, Django comprueba las migraciones y no repite las ya aplicadas. Si el despliegue usa otra imagen o sobrescribe el entrypoint, esta automatización no se ejecutará.

Crear superusuario si hace falta:

```bash
docker compose -f docker-compose.production.example.yml run --rm backend python manage.py createsuperuser
```

### Tareas programadas en producción: mercado y noticias

Cuando la aplicación esté en producción, hay dos procesos que conviene ejecutar de forma programada:

- `refresh_market_data_llm`: refresca los datos del carrusel de mercado.
- `scripts/import_rss_news.py --llm`: descarga e interpreta noticias RSS recientes.

La frecuencia recomendada inicial:

- mercado: una vez al día, fuera de horas de mucho tráfico;
- noticias RSS: cada 1-3 horas si se quiere actualidad frecuente, o una vez al día si se quiere contener coste y volumen editorial.

#### Job de mercado

Qué hace:

- consulta datos recientes de mercado y macro usando Gemini con Google Search grounding;
- devuelve un JSON con símbolos, valores, fechas, fuente y calidad;
- valida que el JSON tenga la estructura esperada;
- imprime un resumen de filas incompletas antes de importar;
- guarda snapshots en base de datos;
- deja métricas de uso del modelo en `_meta.llm` dentro del `raw_response` del run.

Qué no hace:

- no publica consejos de inversión;
- no decide qué comprar o vender;
- no sustituye una fuente oficial de facturación de Google/Gemini;
- no borra snapshots históricos.

Antes de activarlo en cron:

1. Confirmar que la base de datos de producción tiene migraciones aplicadas.
2. Ejecutar `python manage.py seed_financial_products` si los productos de mercado todavía no existen.
3. Configurar `GOOGLE_API_KEY` o `GEMINI_API_KEY` en secrets/variables de producción.
4. Configurar `MARKET_LLM_MODEL`.
5. Opcionalmente configurar `MARKET_LLM_INPUT_USD_PER_1M`, `MARKET_LLM_OUTPUT_USD_PER_1M` y `MARKET_LLM_GOOGLE_SEARCH_USED_THIS_MONTH` para estimaciones internas de coste.
6. Probar primero con `--dry-run --output` y revisar el JSON.
7. Ejecutar una vez sin `--dry-run` y comprobar el endpoint del carrusel en frontend/API.

Prueba manual en el servidor:

```bash
cd /path/to/finanU/backend
python manage.py refresh_market_data_llm --dry-run --output /tmp/market_latest.json
python manage.py refresh_market_data_llm
```

Ejemplo de cron en un servidor Linux con virtualenv:

```cron
# Ejecuta el refresco del carrusel cada día a las 05:15.
15 5 * * * cd /path/to/finanU/backend && /path/to/finanU/backend/.venv/bin/python manage.py refresh_market_data_llm >> /var/log/finanu/marketdata_refresh.log 2>&1
```

Crear el directorio de logs antes de activar el cron:

```bash
sudo mkdir -p /var/log/finanu
sudo chown deploy:deploy /var/log/finanu
```

Ejemplo de cron si el backend corre con Docker Compose:

```cron
# Ejecuta el refresco del carrusel cada día a las 05:15 dentro del servicio backend.
15 5 * * * cd /path/to/finanU && docker compose -f docker-compose.production.example.yml run --rm backend python manage.py refresh_market_data_llm >> /var/log/finanu/marketdata_refresh.log 2>&1
```

En infra cloud, la misma idea puede implementarse con:

- AWS EventBridge Scheduler + ECS/Fargate task;
- Kubernetes CronJob;
- systemd timer;
- cron del host si el despliegue es en una VM.

La tarea programada debe usar la misma imagen/código y las mismas variables de entorno que el backend web, especialmente credenciales de base de datos y API key de Gemini. Si se usa AWS, las claves reales deben venir de AWS Secrets Manager, Parameter Store o variables seguras del servicio, nunca del repositorio.

Observabilidad recomendada:

- guardar stdout/stderr del comando en logs;
- monitorizar si aparece `CommandError`;
- revisar `FinancialDataRun.status`;
- revisar `items_received`, `items_imported`, `items_updated`, `items_failed` y `items_skipped`;
- alertar si el estado queda `FAILED` o si no se importan filas durante varios días;
- revisar periódicamente el uso real en la consola de Google/Gemini, porque el coste impreso por el comando es solo una estimación.

Rollback operativo:

- si el comando falla, el dashboard seguirá mostrando el último snapshot válido disponible;
- si se importa una fila parcial, el servicio puede marcar productos como no destacados cuando el último snapshot no tenga valor utilizable;
- para investigar, ejecutar `--dry-run --output /tmp/market_debug.json` y revisar el payload antes de volver a importar.

#### Job de noticias RSS

Qué hace:

- descarga RSS financieros desde varias fuentes configuradas en `backend/scripts/import_rss_news.py`;
- crea un XML temporal unificado;
- filtra noticias antiguas, duplicadas o ya existentes;
- usa Gemini para traducir, resumir y clasificar cada noticia nueva;
- guarda las noticias como `NewsArticle`;
- imprime métricas de items escaneados, creados, duplicados, antiguos, fallos LLM y tokens.

Qué no hace:

- no reinterpreta noticias ya existentes;
- no publica consejos de inversión;
- no garantiza que todos los RSS respondan en cada ejecución;
- no bloquea todo el import si falla el LLM en una noticia concreta, porque usa fallback heurístico.

Antes de activarlo en cron:

1. Confirmar que `content` tiene migraciones aplicadas.
2. Configurar `GOOGLE_API_KEY` o `GEMINI_API_KEY` si se usará `--llm`.
3. Configurar `NEWS_LLM_MODEL`.
4. Probar manualmente con `--limit` para controlar coste.
5. Revisar que las noticias creadas tengan textos correctos en inglés y polaco.

Prueba manual en el servidor:

```bash
cd /path/to/finanU/backend
python scripts/import_rss_news.py --llm --limit 10 --keep-xml
python scripts/import_rss_news.py --llm
```

Ejemplo de cron en un servidor Linux con virtualenv:

```cron
# Importa e interpreta noticias RSS cada 2 horas.
0 */2 * * * cd /path/to/finanU/backend && /path/to/finanU/backend/.venv/bin/python scripts/import_rss_news.py --llm >> /var/log/finanu/rss_news_import.log 2>&1
```

Ejemplo de cron si el backend corre con Docker Compose:

```cron
# Importa e interpreta noticias RSS cada 2 horas dentro del servicio backend.
0 */2 * * * cd /path/to/finanU && docker compose -f docker-compose.production.example.yml run --rm backend python scripts/import_rss_news.py --llm >> /var/log/finanu/rss_news_import.log 2>&1
```

Si se ejecutan ambos jobs en la misma máquina, conviene dejar logs separados:

```text
/var/log/finanu/marketdata_refresh.log
/var/log/finanu/rss_news_import.log
```

También conviene que no arranquen exactamente en el mismo minuto, para evitar picos innecesarios de API y base de datos.

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
python manage.py seed_learning_catalog
python manage.py seed_learning_content  # alias de seed_learning_catalog
python manage.py seed_financial_products
python manage.py refresh_market_data_llm --dry-run --output market_latest.json
python manage.py refresh_market_data_llm
python scripts/import_rss_news.py --llm --limit 10 --keep-xml
python scripts/import_rss_news.py --llm
```

## API Backend

Base URL:

```text
/api/
```

### Usuarios

```text
POST   /api/users/login/
POST   /api/users/password-reset/
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

Recuperacion de contraseña acepta:

```json
{
  "email": "user@example.com"
}
```

En `DEBUG=True` devuelve `temporary_password`. En produccion genera la contraseña temporal y la envia por email sin exponerla en la respuesta.

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
GET/POST/PATCH/DELETE /api/content/news/
```

`/api/content/news/` expone `NewsArticle`. El frontend lo consume para el feed del dashboard y permite filtrar por `news_type`:

```text
GET /api/content/news/?news_type=crypto,stock_market
```

Los antiguos endpoints `/api/content/articles/`, `/api/content/courses/` y `/api/content/lessons/` fueron retirados junto con sus modelos legacy.

### Marketdata

```text
GET /api/market/products/
GET /api/market/snapshots/latest/
GET /api/market/snapshots/latest/?featured=true&category=CRYPTO&lang=pl
GET /api/market/products/{slug}/history/
```

`marketdata` sustituye a la antigua app `markets`. No gestiona senales de compra/venta: mantiene productos financieros y snapshots educativos para el carrusel.

Modelos principales:

- `FinancialProduct`.
- `FinancialProductSnapshot`.
- `FinancialDataRun`.

Los productos base se cargan con:

```bash
python manage.py seed_financial_products
```

Los valores se refrescan con:

```bash
python manage.py refresh_market_data_llm
```

### Learning

```text
GET /api/learning/catalog/
GET /api/learning/catalog/catalog/?language=en
GET /api/learning/catalog/catalog/?language=pl&user_id={user_id}
GET /api/learning/progress/?user_id={user_id}
POST /api/learning/lessons/{lesson_id}/submit/
```

`learning` expone el catalogo activo por idioma, filtros por categoria/nivel, progreso por usuario y envio de respuestas de quiz. Una leccion solo queda completada si todas las preguntas activas se responden correctamente.

Enviar respuestas de quiz acepta:

```json
{
  "user_id": 1,
  "answers": {
    "10": "42",
    "11": "45"
  }
}
```

Modelos principales:

- `LearningCategory`.
- `CourseType`.
- `LearningLevel`.
- `Course`.
- `Lesson`.
- `LessonQuiz`.
- `LessonQuizQuestion`.
- `LessonQuizOption`.
- `UserLessonProgress`.
- `UserCourseProgress`.

El catalogo inicial se carga o actualiza con:

```bash
python manage.py seed_learning_catalog
```

`seed_learning_content` sigue disponible como alias del mismo comando.

### Privacidad: historial de decisiones de cookies

```text
POST /api/privacy/cookie-consents/
```

El banner registra aceptar, rechazar y guardar preferencias. Cada navegador recibe un `consentId` aleatorio en la cookie `financu_cookie_consent`, conservado entre cambios durante sus 180 días de duración. La política actual es `1.2`, con necesarias siempre activas y analítica opcional. Las cookies de versiones anteriores, sin identificador o con `adsMeasurement` distinto de `false` vuelven a mostrar el aviso, con todos los permisos opcionales denegados hasta una nueva elección. Se conserva cualquier `consentId` válido de la cookie anterior; sus elecciones no se reconstruyen como registros nuevos.

Cada decisión genera un `event_id` UUID distinto. El cuerpo del POST incluye `event_id`, `consent_id`, `action` (`accept_all`, `reject_all` o `custom`), `analytics`, `ads_measurement`, `marketing`, `policy_version`, `language`, `page_path` y `client_recorded_at`. Aceptar todo activa analítica; rechazar todo la desactiva. `ads_measurement` y `marketing` permanecen en `false`, como campos de compatibilidad del historial, y no aparecen como opciones del banner. Abrir o cancelar los ajustes no genera eventos.

`analytics` controla `analytics_storage`. `ad_storage`, `ad_user_data` y `ad_personalization` permanecen siempre `denied` en esta aplicación, incluso ante preferencias antiguas o manipuladas. `adsMeasurement` y `marketing` se guardan como `false` en la cookie. El arranque anterior a GTM y las actualizaciones aplican la misma correspondencia. Se mantiene Consent Mode avanzado, por lo que Google puede recibir señales sin cookies cuando los permisos están denegados. Se sigue la [guía de Consent Mode de Google](https://developers.google.com/tag-platform/security/guides/consent). La política enlaza a la información sobre el uso de datos por Google desde su introducción.

El endpoint admite las políticas `1.0`, `1.1` y `1.2`; rechaza las demás. `1.2` exige `ads_measurement: false` y valida la acción según analítica. Los eventos históricos `1.1` conservan sus categorías y validación anteriores: aceptar todo requiere analítica y medición publicitaria activas; rechazar todo requiere ambas desactivadas; configurar permite las cuatro combinaciones. `1.0` valida solo analítica y completa `ads_measurement` con `false` si falta. Así pueden llegar eventos pendientes del frontend anterior y reintentarse registros previos sin duplicarlos. La cola no cambia la versión, fecha, identificador ni contenido de los eventos históricos; estos registros no conceden permisos actuales a Google.

El servidor añade su fecha de recepción, la IP truncada a `/24` en IPv4 o `/48` en IPv6 y el user-agent limitado a 512 caracteres. No vincula el registro a una cuenta ni guarda parámetros o fragmentos de la URL. El endpoint permite POST antes del login y no ofrece una consulta pública del historial.

- `201`: decisión nueva registrada.
- `200`: reintento del mismo evento, con los mismos datos; devuelve el registro original.
- `409`: el identificador del evento ya existe con datos distintos.
- `400`: datos inválidos o categorías incompatibles con la acción.
- `429`: límite de peticiones alcanzado, configurable mediante `DRF_COOKIE_CONSENT_RATE` (por defecto `120/hour`).

La elección se aplica inmediatamente. Una cola local conserva como máximo las 10 decisiones pendientes más recientes y reintenta al abrir la aplicación, recuperar conexión o guardar otra decisión. Los fallos de red, `408`, `429` y errores del servidor quedan pendientes; los errores definitivos se descartan. Si el almacenamiento local está bloqueado, se intenta el envío directamente, sin garantía de reintento tras cerrar la página. Un mismo evento conserva su identificador durante todos sus reintentos.

El historial está en `/admin/` → **Registros de consentimiento de cookies**, con búsqueda por `consent_id` o `event_id` y filtros por acción, categorías, política y fecha. El permiso de consulta permite ver lista y detalle; las altas y modificaciones manuales están deshabilitadas. La eliminación requiere el permiso correspondiente de Django. No se ha añadido un borrado automático; los registros del servidor son independientes de la caducidad de la cookie.

Para actualizar el backend, aplicar las migraciones con el entorno y base de datos del despliegue:

```bash
python manage.py migrate --noinput
```

La migración `privacy.0001_initial` crea la tabla y la restricción única del evento. `privacy.0002_cookieconsentrecord_ads_measurement` añade el campo histórico de medición publicitaria, con `false` para los registros anteriores. La imagen Docker existente ejecuta este comando al arrancar. Publicar primero el backend y completar la migración; después publicar el frontend `1.2`. Durante el despliegue, el backend seguirá aceptando eventos históricos `1.0` y `1.1`. Si `0002` ya está aplicada, `1.2` no necesita una migración adicional. El sistema de estilos continúa usando la configuración actual.

Comprobaciones locales (los tests usan una base de datos aislada):

```bash
cd backend
DB_ENGINE=sqlite REDIS_URL= .venv/bin/python manage.py test privacy --noinput
DB_ENGINE=sqlite REDIS_URL= .venv/bin/python manage.py makemigrations --check --dry-run
```

En `frontend/`, ejecutar `npm test` y `npm run build`. En el navegador, verificar aceptar/rechazar, guardar analítica activada o desactivada y sus registros en el admin; también la renovación de cookies `1.0`/`1.1`, que ningún permiso publicitario se conceda, la reapertura/cancelación de preferencias y los reintentos. Consultar la política no guarda ninguna decisión. Revisar móvil y escritorio, navegación con teclado y desplazamiento del panel con las acciones visibles.

### Registro en el producto y separación de dominios

Las campañas en Polonia aterrizan en `lkoneservice.com/dmfu2/` (operadores `TM`, `PA`, `PU`, `OR`). El pago se confirma allí antes de enviar al usuario a `financuinvestors.com`. La aplicación mide únicamente el registro completado en Analytics y Django; no envía conversiones a Google Ads ni necesita enlazar ambos dominios para atribución publicitaria.

Django ya conserva el registro operativo en `UserProfile.created_at` y `SubscriptionEntitlement.registered_at`, una vez validada y consumida la suscripción elegible. No depende del consentimiento analítico ni necesita otra tabla de tracking. Tras la respuesta satisfactoria del alta, el frontend prepara `{ event: 'financu_sign_up', method: 'email' }` una sola vez por formulario, antes de navegar al onboarding y solo si sigue aceptada la analítica. El evento no se emite al enviar un formulario fallido, recargar o volver a entrar; no se recupera retroactivamente si el consentimiento llega después. No incluye email, teléfono, identificadores, token ni importe. Un fallo de tracking no interrumpe el registro.

Configuración pendiente en GTM/GA4 (no publicada por este cambio):

- Contenedor de la aplicación: `GTM-NV2H49ZG`. Flujo GA4: `G-F42XR6C80F` (propiedad `557584014`). En la revisión del 21/10/2026, la versión publicada del contenedor estaba vacía; la etiqueta de Google solo existía en el borrador. El flujo indicaba que no había recibido datos en las últimas 48 horas.
- Conservar la etiqueta de Google del borrador para ese flujo y añadir una etiqueta **Google Analytics: evento de GA4** con nombre de evento `sign_up`, parámetro fijo `method = email` y activador de evento personalizado `financu_sign_up`. Exigir además `analytics_storage` para este evento, de modo que una revocación anterior a procesar la cola evite su envío.
- Probar en Vista previa y DebugView un alta válida, un error, doble envío, rechazo y retirada de consentimiento durante el alta. Publicar tras desplegar el backend/frontend correspondiente. El evento preparado en código no aparecerá en Analytics hasta configurar y publicar la etiqueta.
- Mantener la propiedad sin exportar este evento a Google Ads, sin audiencias de remarketing ni Google Signals para publicidad. El registro puede marcarse como evento clave de GA4 para informes internos.
- Verificar que se mantienen ocultos los parámetros `token`, `email`, `user_id` y `account_id` en GA4 y que no se añaden datos personales a parámetros de eventos.

La landing carga Google Ads `AW-18226103401` en la página revisada. Su consentimiento, conversiones de pago, avisos y verificaciones del anunciante deben revisarse por separado con el responsable de `lkoneservice.com`; el banner de la aplicación no gestiona ese dominio. No se ha modificado la landing ni su configuración publicitaria. Confirmar también las razones sociales: la landing muestra `NOVADIGITAL STUDIO 2 S.L.` y la política actual de la aplicación muestra `NOVADIGITAL STUDIO SLU`; no se deben unificar sin confirmar quién opera cada parte. Antes de publicar, conservar una copia de los textos y elecciones de cada versión de la política junto con su fecha de entrada en vigor.

### Endpoints retirados

Estos endpoints ya no forman parte del backend activo:

```text
/api/markets/assets/
/api/markets/signals/
/api/subscriptions/
/api/content/articles/
/api/content/courses/
/api/content/lessons/
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
- ViewSets/APIViews DRF: endpoints para usuarios, noticias, catalogo Learning, progreso y datos de mercado.
- Password hashing: las contraseñas se guardan hasheadas con utilidades de Django.
- CORS: configurado por variables de entorno para desarrollo local y red local.
- Throttling DRF: scopes para login, signup, perfiles, settings, onboarding y recuperacion de contraseña.
- Redis opcional: recomendado en produccion si hay mas de un worker/instancia para compartir contadores de throttle.

## Limitaciones Conocidas

- La autenticación es simple y no usa JWT ni sesiones server-side.
- Learning sincroniza progreso con backend cuando hay usuario; el frontend mantiene datos locales como fallback.
- El feed de noticias y el carrusel de mercado dependen de imports/jobs para mantenerse frescos.
- Algunos módulos backend exponen CRUD abierto porque DRF está configurado con `AllowAny`.
- Hay tests backend para usuarios, noticias, learning y marketdata, pero falta ampliar cobertura frontend/e2e y permisos por usuario.

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

- Reforzar permisos y ownership en los endpoints de `learning`.
- Añadir autenticación real con tokens.
- Añadir permisos por usuario en settings y progreso.
- Configurar email real para recuperacion de contraseña antes de produccion.
- Configurar Redis si el backend se despliega con varios workers o instancias.
- Retirar definitivamente las apps legacy `markets` y `subscriptions` cuando todos los entornos hayan aplicado sus migraciones de borrado.
- Ampliar tests de integración y añadir cobertura frontend/e2e.
- Internacionalizar respuestas de error del backend.
- Añadir panel admin editorial para noticias, cursos y quizzes.
