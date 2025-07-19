# backend/apps/participants/tasks.py
import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from django.utils.translation import gettext as _

from .models import Participation

logger = logging.getLogger(__name__)


# ==============================================================================
# LÓGICA DE NEGOCIO (ASÍNCRONA PURA)
# ==============================================================================
async def _cleanup_expired_participation_async_logic(participation_id: int):
    """
    Contiene el núcleo de la lógica asíncrona para limpiar participaciones expiradas.
    """
    try:
        # Usamos .select_related('payment').aget() para una obtención asíncrona y eficiente.
        # Esto precarga la relación de pago en la misma consulta.
        participation = await Participation.objects.select_related("payment").aget(
            pk=participation_id
        )

        # La forma más segura de comprobar es ver si el campo 'payment' (la relación) es None.
        # Como hemos hecho select_related, esta comprobación no causa una consulta adicional.
        if participation.payment is None:
            logger.warning(
                _("Participation %(id)d has expired without a payment. Deleting.")
                % {"id": participation_id}
            )
            # .adelete() es la versión asíncrona de .delete()
            await participation.adelete()
            logger.info(
                _("Participation %(id)d successfully deleted.")
                % {"id": participation_id}
            )
        else:
            logger.info(
                _("Participation %(id)d has a payment reported. No action taken.")
                % {"id": participation_id}
            )

    except Participation.DoesNotExist:
        # Este es un caso normal si el pago se procesó o la participación se eliminó
        # por otros medios. No es un error.
        logger.info(
            _("Participation %(id)d not found. Already processed or deleted.")
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
