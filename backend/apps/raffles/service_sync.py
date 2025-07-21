# backend/apps/raffles/services.py

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from tickets.models import Ticket

from .models import Draw, Prize

logger = logging.getLogger(__name__)


class DrawProcessingError(Exception):
    """Excepción personalizada para errores en el procesamiento del sorteo."""

    pass


class RevokePrizeError(Exception):
    """Excepción para errores al revocar un premio."""

    pass


@transaction.atomic
def process_draw_result(draw: Draw, winning_number: int) -> str:
    """
    Procesa el resultado de un sorteo de forma atómica y segura.
    """
    # ✅ DEFINITIVO: Comparamos con el string "SCHEDULED"
    if draw.status != "SCHEDULED":
        raise DrawProcessingError(
            f"El sorteo ID {draw.id} no está programado. Estado actual: {draw.status}."
        )

    prize = draw.prize
    if prize.winner_participation is not None:
        raise DrawProcessingError(f"El premio '{prize.name}' ya ha sido asignado.")

    raffle = prize.raffle
    draw.winning_number = winning_number

    try:
        winning_ticket = Ticket.objects.select_related("participation").get(
            raffle=raffle, ticket_number=winning_number
        )

        logger.info(
            f"Ganador encontrado para el sorteo {draw.id}. Ticket: {winning_number}, Participante: {winning_ticket.participation.id}"
        )

        prize.winner_participation = winning_ticket.participation
        prize.winner_ticket_number = winning_number
        prize.save()

        # ✅ DEFINITIVO: Asignamos el string "COMPLETED"
        draw.status = "COMPLETED"
        draw.save()

        return f"¡Ganador encontrado! El premio '{prize.name}' ha sido asignado al participante {winning_ticket.participation.full_name}."

    except Ticket.DoesNotExist:
        logger.warning(
            f"No se encontró ganador para el sorteo {draw.id} con el número {winning_number}. Iniciando rollover."
        )

        # ✅ DEFINITIVO: Asignamos el string "ROLLED_OVER"
        draw.status = "ROLLED_OVER"
        draw.save()

        new_draw_time = draw.draw_time + timedelta(days=1)
        Draw.objects.create(
            prize=prize,
            lottery_name=draw.lottery_name,
            draw_time=new_draw_time,
            # ✅ DEFINITIVO: Asignamos el string "SCHEDULED"
            status="SCHEDULED",
        )

        return f"No se encontró un ticket con el número {winning_number}. El premio se acumula para un nuevo sorteo programado para el {new_draw_time.strftime('%Y-%m-%d %H:%M')}."


@transaction.atomic
def revoke_prize_assignment(prize: Prize):
    """
    Lógica de negocio centralizada para revocar un premio y reprogramar su sorteo.
    Esta función es atómica y segura.

    Args:
        prize: La instancia del Premio a revocar.

    Raises:
        RevokePrizeError: Si el premio no puede ser revocado (no asignado, ya entregado, etc.).
    """
    # 1. Validación
    if not prize.winner_participation:
        raise RevokePrizeError(
            f"El premio '{prize.name}' no tiene un ganador asignado."
        )
    if prize.is_delivered:
        raise RevokePrizeError(
            f"No se puede revocar el premio '{prize.name}' porque ya fue entregado."
        )

    # 2. Encontrar y actualizar el sorteo completado
    completed_draw = (
        Draw.objects.filter(prize=prize, status="COMPLETED")
        .order_by("-draw_time")
        .first()
    )
    if not completed_draw:
        raise RevokePrizeError(
            f"No se encontró un sorteo 'Completado' asociado al premio '{prize.name}'. La operación no puede continuar."
        )

    # 3. Ejecutar la lógica de revocación
    # Resetear el premio
    prize.winner_participation = None
    prize.winner_ticket_number = None
    prize.save()

    # Marcar el sorteo original como "Rolled Over" para auditoría
    completed_draw.status = "ROLLED_OVER"
    completed_draw.save()

    # Crear un nuevo sorteo para el futuro
    new_draw_time = timezone.now() + timedelta(days=1)
    Draw.objects.create(
        prize=prize,
        lottery_name=completed_draw.lottery_name,
        draw_time=new_draw_time,
        status="SCHEDULED",
    )
