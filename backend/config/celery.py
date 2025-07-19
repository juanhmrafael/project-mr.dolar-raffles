# backend/config/celery.py
# ========================
# Propósito: Archivo de configuración para Celery.
# Este archivo define la instancia de la aplicación Celery y la configura
# para que funcione con nuestro proyecto Django.
import os
import sys
from pathlib import Path

from celery import Celery

# Obtener la ruta raíz del proyecto (backend/)
# Path(__file__) es este archivo (celery.py)
# .parent es 'config'
# .parent es 'backend'
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Esto es CRUCIAL para que Celery pueda encontrar los módulos de las apps
# como 'utils', 'participants', etc.
sys.path.append(str(PROJECT_ROOT / "apps"))
# Asegurarse de que el entorno de Django esté configurado ANTES de importar Celery
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.development"),
)


# Propósito: Crear la instancia de la aplicación Celery.
# El primer argumento, 'config', es el nombre del módulo actual. Es una convención.
app = Celery("config")

# Propósito: Configurar Celery usando los settings de Django.
# El argumento 'namespace="CELERY"' significa que Celery buscará todas sus variables
# de configuración en nuestro archivo settings.py que comiencen con el prefijo "CELERY_".
# Por ejemplo: CELERY_BROKER_URL, CELERY_RESULT_BACKEND, etc.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Propósito: Descubrir y cargar automáticamente las tareas definidas en nuestras apps de Django.
# Celery buscará un archivo llamado 'tasks.py' en cada una de las aplicaciones
# listadas en INSTALLED_APPS y registrará cualquier tarea que encuentre allí.
app.autodiscover_tasks()


# (Opcional, pero útil para depuración)
# Propósito: Una tarea de ejemplo para verificar que Celery está funcionando.
# Puedes ejecutarla desde el shell de Django para probar la conexión.
@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
