# settings/base.py (Versión Final Definitiva - Auditada y Corregida)

from pathlib import Path

from celery.schedules import crontab
from decouple import Csv, config
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- BLOQUE 1: LECTURA DE CONFIGURACIÓN Y SECRETOS ---
# ----------------------------------------------------------------
# Decouple lee del entorno, que es poblado por el entrypoint.sh.

# Secretos (leídos de /run/secrets/)
SECRET_KEY = config("SECRET_KEY")
FIELD_ENCRYPTION_KEY = config("FIELD_ENCRYPTION_KEY")
REDIS_PASSWORD = config("REDIS_PASSWORD")

# Configuración no secreta (leída de .env)
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())
REDIS_USER = config("REDIS_USER", default="appuser")
REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = config("REDIS_PORT")


# --- BLOQUE 2: CONSTRUCCIÓN SEGURA DE URIs DE CONEXIÓN ---
# ----------------------------------------------------------------
# Se construyen las URIs completas de forma explícita para evitar errores de parsing.

CELERY_BROKER_URL = f"redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
FINAL_CACHE_URL = f"redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1"
FINAL_CACHE_SELECT2_URL = (
    f"redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/2"
)


# --- BLOQUE 3: CONFIGURACIÓN DE APLICACIONES DE DJANGO ---
# ----------------------------------------------------------------

# Application definition
INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "adrf",
    "corsheaders",
    "django_celery_results",
    "drf_spectacular",
    "simple_history",
    "encrypted_model_fields",
    "rangefilter",
    "django_select2",
    "django_celery_beat",
    "utils.apps.UtilsConfig",
    "users.apps.UsersConfig",
    "raffles.apps.RafflesConfig",
    "participants.apps.ParticipantsConfig",
    "payments.apps.PaymentsConfig",
    "tickets.apps.TicketsConfig",
    "currencies.apps.CurrenciesConfig",
    "auditing.apps.AuditingConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGES = [("en", _("English")), ("es", _("Spanish"))]
LOCALE_PATHS = [BASE_DIR / "locale"]
LANGUAGE_CODE = "es"
AUTH_USER_MODEL = "users.CustomUser"
TIME_ZONE = "America/Caracas"
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# Configuración de Caché
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": FINAL_CACHE_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
    "select2": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": FINAL_CACHE_SELECT2_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
}
SELECT2_CACHE_BACKEND = "select2"

# Configuración de Ratelimit
RATELIMIT_USE_CACHE = "default"

# Configuración de Celery
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_RESULT_EXTENDED = True
CELERY_TASK_TRACK_STARTED = True

MIGRATION_MODULES = {
    "auth": "users.migrations_auth",
    "django_celery_results": "users.migrations_celery",
}

# Configuración de Celery Beat
CELERY_BEAT_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    "update-bcv-rate-afternoons": {
        "task": "currencies.update_bcv_rate",
        "schedule": crontab(minute="0", hour="17", day_of_week="1-5"),
    },
}
