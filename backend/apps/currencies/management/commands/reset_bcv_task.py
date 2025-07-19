# backend/apps/currencies/management/commands/reset_bcv_task.py
from datetime import date

from django.core.cache import cache
from django.core.management.base import BaseCommand

from currencies.models import ExchangeRate

# ✅ IMPORTACIÓN CLAVE: Importamos la constante desde el archivo de tareas
# para garantizar que siempre usemos la misma plantilla de clave.
from currencies.tasks import CACHE_KEY_ATTEMPTS_TEMPLATE


class Command(BaseCommand):
    """
    Comando de gestión para resetear el estado de la tarea diaria de actualización del BCV.

    - Elimina las tasas de cambio futuras de la base de datos.
    - Elimina el contador de intentos de la caché para el día actual.
    """

    help = "Resets the state for the daily BCV update task for today."

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.WARNING(
                "--- Reseteando el estado de la tarea de actualización del BCV ---"
            )
        )

        # --- 1. Resetear la Base de Datos ---
        deleted_count, _ = ExchangeRate.objects.filter(date__gt=date.today()).delete()
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Base de Datos: Se eliminaron {deleted_count} tasas futuras."
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    "Base de Datos: No se encontraron tasas futuras que borrar."
                )
            )

        # --- 2. Resetear la Caché ---
        # ✅ LÓGICA MEJORADA: Construimos la clave usando la constante importada.
        today_str = date.today().isoformat()
        cache_key = CACHE_KEY_ATTEMPTS_TEMPLATE.format(today_str)

        result = cache.delete(cache_key)
        if result:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Caché: Se eliminó la clave '{cache_key}'. Contador de intentos reseteado."
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f"Caché: La clave '{cache_key}' no existía en la caché."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\n🚀 ¡Sistema listo para una nueva prueba de ciclo completo!"
            )
        )
