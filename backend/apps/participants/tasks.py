# backend/apps/participants/tasks.py
import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from django.utils.translation import gettext as _
from payments.models import Payment

from .models import Participation

logger = logging.getLogger(__name__)


# ==============================================================================
# LÓGICA DE NEGOCIO (ASÍNCRONA PURA)
# ==============================================================================
async def _cleanup_expired_participation_async_logic(participation_id: int):
    """
    Contiene el núcleo de la lógica asíncrona para limpiar participaciones expiradas.
    SOLUCIÓN FINAL: Usa una comprobación de existencia explícita y asíncrona.
    """
    try:
        # ✅ PASO 1: Comprobar la existencia del pago de forma explícita y asíncrona.
        # Esto traduce la pregunta "¿Existe un pago para esta participación?"
        # directamente a una consulta asíncrona eficiente (SELECT 1 ... LIMIT 1).
        payment_exists = await Payment.objects.filter(
            participation_id=participation_id
        ).aexists()

        if payment_exists:
            # Si el pago existe, no hacemos nada.
            logger.info(
                _("Participation %(id)d has a payment reported. No action taken.")
                % {"id": participation_id}
            )
            return  # Salimos de la función tempranamente.

        # ✅ PASO 2: Si el pago NO existe, procedemos a eliminar la participación.
        # Obtenemos la participación solo si sabemos que necesitamos actuar sobre ella.
        try:
            participation = await Participation.objects.aget(pk=participation_id)
            logger.warning(
                _("Participation %(id)d has expired without a payment. Deleting.")
                % {"id": participation_id}
            )
            # .adelete() es la versión asíncrona y correcta de .delete()
            await participation.adelete()
            logger.info(
                _("Participation %(id)d successfully deleted.")
                % {"id": participation_id}
            )
        except Participation.DoesNotExist:
            # Es posible que la participación ya haya sido eliminada entre la comprobación
            # de aexists y el aget, lo cual es un caso normal.
            logger.info(
                _("Participation %(id)d not found for deletion. Already processed.")
                % {"id": participation_id}
            )

    except Exception as e:
        # Capturamos cualquier otro error inesperado para tener visibilidad.
        logger.error(
            _(
                "An unexpected error occurred during cleanup for participation %(id)d: %(error)s"
            )
            % {"id": participation_id, "error": e},
            exc_info=True,
        )


# ==============================================================================
# TAREA DE CELERY (SÍNCRONA - PUNTO DE ENTRADA)
# ==============================================================================
@shared_task(name="participants.cleanup_expired_participation")
def cleanup_expired_participation(participation_id: int):
    """
    Punto de entrada síncrono para Celery.
    Ejecuta la lógica de limpieza asíncrona en un bucle de eventos.
    """
    # Usamos async_to_sync para puentear del mundo síncrono de Celery al
    # mundo asíncrono de nuestra lógica de aplicación.
    return async_to_sync(_cleanup_expired_participation_async_logic)(participation_id)
