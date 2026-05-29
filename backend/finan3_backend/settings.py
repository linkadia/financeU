from pathlib import Path
from os import getenv

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_list(name, default=""):
    return [item.strip() for item in getenv(name, default).split(",") if item.strip()]


def env_bool(name, default=False):
    return getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

SECRET_KEY = getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "users",
    "content",
    "markets",
    "subscriptions",
    "learning",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "finan3_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "finan3_backend.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    *env_list("CORS_ALLOWED_ORIGINS"),
]

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Development keeps a local in-memory cache so the app starts without Redis.
# Production can set REDIS_URL to share throttle counters across app workers.
REDIS_URL = getenv("REDIS_URL")
CACHES = {
    "default": (
        {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": env_bool("DJANGO_REDIS_IGNORE_EXCEPTIONS", True),
            },
        }
        if REDIS_URL
        else {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "finanu-dev-cache",
        }
    )
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": getenv("DRF_ANON_RATE", "100/hour"),
        "user": getenv("DRF_USER_RATE", "5000/hour"),
        "login": getenv("DRF_LOGIN_RATE", "10/minute"),
        "login_user_ip": getenv("DRF_LOGIN_USER_IP_RATE", "5/minute"),
        "signup": getenv("DRF_SIGNUP_RATE", "20/hour"),
        "profiles": getenv("DRF_PROFILES_RATE", "120/minute"),
        "settings": getenv("DRF_SETTINGS_RATE", "30/hour"),
        "onboarding": getenv("DRF_ONBOARDING_RATE", "60/hour"),
    },
    # Trust exactly one proxy/load balancer hop when resolving X-Forwarded-For.
    "NUM_PROXIES": int(getenv("DRF_NUM_PROXIES", "1")),
    "EXCEPTION_HANDLER": "finan3_backend.exceptions.custom_exception_handler",
}
