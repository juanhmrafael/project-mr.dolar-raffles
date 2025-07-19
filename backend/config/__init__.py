# backend/config/__init__.py
# ==========================
# Propósito: Asegurar que la aplicación Celery se cargue cuando Django se inicie.
# Esto es necesario para que el decorador @shared_task funcione correctamente.

from .celery import app as celery_app

# Propósito: Exponer la aplicación Celery para que pueda ser utilizada en otras partes del proyecto.
__all__ = ("celery_app",)
