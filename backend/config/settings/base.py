from pathlib import Path

from celery.schedules import crontab
from decouple import Csv, config
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

REDIS_USER = config("REDIS_USER", default="appuser")
REDIS_PASSWORD = config("REDIS_PASSWORD")

# Application definition

INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # --- Apps de Terceros ---
    "rest_framework",
    "adrf",
    "corsheaders",
    "django_celery_results",
    "drf_spectacular",  # Para la documentación de la API (OpenAPI)
    "simple_history",  # Para el historial de cambios y auditoría
    "encrypted_model_fields",
    "rangefilter",
    "django_select2",
    "django_celery_beat",
    # --- Nuestras Apps ---
    "utils.apps.UtilsConfig",
    "users.apps.UsersConfig",
    "raffles.apps.RafflesConfig",
    "participants.apps.ParticipantsConfig",
    "payments.apps.PaymentsConfig",
    "tickets.apps.TicketsConfig",
    "currencies.apps.CurrenciesConfig",
    "auditing.apps.AuditingConfig",
    # Para orden en archivos staticos
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    # --- Para django-simple-history ---
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # ¡Importante para traducciones!
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# Punto de entrada para servidores síncronos (WSGI).
WSGI_APPLICATION = "config.wsgi.application"

# Punto de entrada para servidores asíncronos (ASGI).
# Esencial para que Django y sus componentes funcionen correctamente
# cuando son servidos por Uvicorn/Daphne.
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
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Idiomas disponibles
LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
]

# Directorio para archivos de traducción
LOCALE_PATHS = [
    BASE_DIR / "locale",
]

LANGUAGE_CODE = "es"

AUTH_USER_MODEL = "users.CustomUser"

# Zona horaria (Venezuela)
TIME_ZONE = "America/Caracas"

# Configuraciones de internacionalización
USE_I18N = True  # Habilitar internacionalización
USE_L10N = True  # Usar formatos locales
USE_TZ = True  # Usar zonas horarias

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Lista de directorios donde Django buscará archivos estáticos adicionales,
# además de los directorios 'static' dentro de cada app.
# Aquí es donde debes poner los estáticos de tu proyecto (logos, CSS global, etc.).
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Configuración de medios (MEDIA)
MEDIA_URL = "/media/"  # URL base para acceder a los archivos multimedia
MEDIA_ROOT = BASE_DIR / "mediafiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv())

# Le dice a Django que confíe en las peticiones POST que vienen de localhost en el puerto 80.
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())

CACHE_URL_TEMPLATE = config("CACHE_URL")
CACHE_SELECT2_URL_TEMPLATE = config("CACHE_SELECT2_URL")
CELERY_BROKER_URL_TEMPLATE = config("CELERY_BROKER_URL")

def build_redis_uri(template: str) -> str:
    """Función auxiliar para construir la URI de Redis con credenciales."""
    # Descomponer la URL base para insertar las credenciales
    scheme, rest = template.split("://")
    return f"{scheme}://{REDIS_USER}:{REDIS_PASSWORD}@{rest}"

FINAL_CACHE_URL = build_redis_uri(CACHE_URL_TEMPLATE)
FINAL_CACHE_SELECT2_URL = build_redis_uri(CACHE_SELECT2_URL_TEMPLATE)
CELERY_BROKER_URL = build_redis_uri(CELERY_BROKER_URL_TEMPLATE)

# --- CONFIGURACIÓN DE CACHÉ (PARA DJANGO-RATELIMIT Y OTROS USOS) ---
# Propósito: Define el backend de caché que Django usará.
# django-ratelimit REQUIERE un backend de caché como Redis o Memcached.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": FINAL_CACHE_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    "select2": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": FINAL_CACHE_SELECT2_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}


# ✅ CONFIGURACIÓN CENTRALIZADA PARA DJANGO-SELECT2
SELECT2_CACHE_BACKEND = "select2"

# --- CONFIGURACIÓN DE DJANGO-RATELIMIT ---
# Propósito: Define cómo se comportará la limitación de tasa.
RATELIMIT_USE_CACHE = "default"  # Le dice a ratelimit que use nuestro caché 'default'.

# --- CONFIGURACIÓN DE CELERY (VERSIÓN MODERNA Y OPTIMIZADA) ---
# Propósito: Define la configuración que Celery usará para conectarse y operar.
# Esta configuración utiliza la nomenclatura moderna en minúsculas, recomendada por la documentación de Celery 5.x.
# Celery leerá estas variables gracias a la línea app.config_from_object en celery.py.

# Propósito: La URL del broker de mensajes (Redis).
# Celery usa esto para enviar y recibir tareas.
# La variable de entorno REDIS_URL debe ser definida en tus archivos .env y .env.prod.
# Ejemplo: REDIS_URL=redis://redis_dev:6379/0
CELERY_BROKER_URL = config("REDIS_URL")

# Propósito: La URL del backend de resultados.
# Celery usa esto para almacenar el estado y los resultados de las tareas.
# Usaremos Redis para esto también por simplicidad.
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Propósito: Formato de serialización para los datos de las tareas.
# 'json' es un formato seguro, estándar y recomendado.
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Propósito: Zona horaria para las tareas.
# Es una buena práctica que coincida con la TIME_ZONE de Django para evitar confusiones.
CELERY_TIMEZONE = TIME_ZONE

# Propósito: Habilitar el almacenamiento de metadatos extendidos para las tareas.
# Guarda información como los argumentos de la tarea, el worker que la ejecutó, etc.
# Es extremadamente útil para la auditoría y la depuración.
CELERY_RESULT_EXTENDED = True

# Propósito: Habilitar el seguimiento del estado 'STARTED' de las tareas.
# Por defecto, Celery solo reporta 'PENDING' o 'SUCCESS'/'FAILURE'.
# Con esto activado, sabrás exactamente cuándo un worker ha comenzado a ejecutar una tarea.
CELERY_TASK_TRACK_STARTED = True

MIGRATION_MODULES = {
    "auth": "users.migrations_auth",
    "django_celery_results": "users.migrations_celery",
}
FIELD_ENCRYPTION_KEY = config("FIELD_ENCRYPTION_KEY")

CELERY_BEAT_TIMEZONE = TIME_ZONE

# ✅ CONFIGURACIÓN DE CELERY BEAT
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_BEAT_SCHEDULE = {
    "update-bcv-rate-afternoons": {  # Nombre más descriptivo
        "task": "currencies.update_bcv_rate",  # ✅ Apunta a la nueva tarea maestra
        "schedule": crontab(
            minute="0",
            hour="17",  # Solo a las 5 PM
            day_of_week="1-5",  # Lunes a Viernes
        ),
    },
}