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

FinanU también puede importar noticias financieras recientes desde varios RSS públicos. Este proceso sirve para alimentar el contenido educativo y de actualidad que verá el usuario en el feed.

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

Por defecto solo importa noticias desde el primer día del mes actual. Se puede cambiar con:

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
    finanu_backend/      Configuración Django y urls raíz
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
  - `finanu_learning_progress`: progreso de aprendizaje.

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
- `NEWS_MIN_PUBLISHED_AT` es opcional. Si no se configura, el script usa el primer día del mes actual.

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
python manage.py loaddata initial_learning_data
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

El módulo `learning` contiene modelos completos para catálogo, lecciones, quizzes y progreso. Actualmente no está enlazado en `finanu_backend/urls.py`, por lo que no expone endpoints REST públicos todavía.

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
