# backend/apps/currencies/tasks.py
import logging
from datetime import date

from asgiref.sync import async_to_sync, sync_to_async
from celery import shared_task
from django.core.cache import cache
from utils.bcv_scrapers import BCVScraper

from .models import ExchangeRate

logger = logging.getLogger(__name__)

# --- Constantes para la Lógica de la Tarea ---
MAX_ATTEMPTS = 5
CACHE_KEY_ATTEMPTS_TEMPLATE = "bcv_update_attempts_{}"  # Plantilla para la clave diaria
CACHE_TIMEOUT_SECONDS = 60 * 60 * 8  # 8 horas, cubre la ventana de 5-9 PM


# ==============================================================================
# LÓGICA DE NEGOCIO (ASÍNCRONA PURA)
# Esta función contiene todo el "trabajo". Es una corutina que no sabe nada
# sobre Celery, lo que la hace testeable y reutilizable.
# ==============================================================================
async def _update_bcv_rate_async_logic():
    """
    Contiene el núcleo de la lógica asíncrona para actualizar la tasa del BCV.
    """
    from django.utils.translation import gettext as _
    today = date.today()
    cache_key = CACHE_KEY_ATTEMPTS_TEMPLATE.format(today.isoformat())

    # --- PASO 1: VERIFICACIONES DE ESTADO (Óptimas y Rápidas) ---

    # Verificación #1.1: Intentos (lectura de caché asíncrona)
    attempt_num = await cache.aget(cache_key, 0) + 1
    logger.info(
        _("Executing BCV rate check. Attempt %(attempt)d of %(max)d for today.")
        % {"attempt": attempt_num, "max": MAX_ATTEMPTS}
    )
    if attempt_num > MAX_ATTEMPTS:
        logger.warning(_("Maximum attempts for today reached. Stopping execution."))
        return _("Max attempts reached.")

    # Verificación #1.2: Éxito Previo (consulta a BD asíncrona)
    if await ExchangeRate.objects.filter(date__gt=today).aexists():
        logger.info(
            _("SUCCESS: A future rate already exists. Task complete for today.")
        )
        return _("Future rate already exists.")

    # Si pasamos las verificaciones, actualizamos el contador para esta ejecución
    await cache.aset(cache_key, attempt_num, CACHE_TIMEOUT_SECONDS)

    # --- PASO 2: EJECUCIÓN DEL TRABAJO COSTOSO (Scraping) ---
    try:
        scraper = BCVScraper()
        # El scraper es síncrono, por lo que lo ejecutamos en un hilo separado
        # para no bloquear el bucle de eventos.
        data = await sync_to_async(scraper.get_processed_data, thread_sensitive=False)()

        if data is None:
            raise Exception(_("Scraper returned None, could not parse page."))

        rate_date = data["date"]

        if rate_date <= today:
            raise Exception(_("BCV has not published a future rate yet."))

        usd_rate = data["rates"].get("USD")
        if not usd_rate:
            raise Exception(_("Scraper succeeded but USD rate was not found."))

        # --- PASO 3: GUARDADO EN BASE DE DATOS (Asíncrono e Idempotente) ---
        object_exchange, created = await ExchangeRate.objects.aget_or_create(
            date=rate_date, defaults={"rate": usd_rate, "source": "BCV_SCRAPER"}
        )
        if created:
            msg = _("SUCCESS: Created new rate for %(date)s.") % {"date": rate_date}
            logger.info(msg)
            return msg
        else:
            msg = _("INFO: Rate for %(date)s already existed.") % {"date": rate_date}
            logger.info(msg)
            return msg

    except Exception as e:
        logger.warning(
            _("Attempt %(attempt)d failed: %(error)s")
            % {"attempt": attempt_num, "error": e}
        )
        return _("Attempt failed.")


# ==============================================================================
# TAREA DE CELERY (SÍNCRONA)
# Este es el punto de entrada que Celery conoce. Su única misión es
# actuar como un "puente" al mundo asíncrono.
# ==============================================================================
@shared_task(name="currencies.update_bcv_rate")
def update_bcv_rate():
    """
    Punto de entrada síncrono para Celery.
    Ejecuta la lógica de negocio asíncrona en un bucle de eventos.
    """
    # async_to_sync es la forma canónica de llamar a código async desde un
    # contexto síncrono. Inicia/usa un bucle de eventos, ejecuta la corutina,
    # espera a que termine, y devuelve su resultado.
    return async_to_sync(_update_bcv_rate_async_logic)()