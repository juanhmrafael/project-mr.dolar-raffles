# backend/apps/tickets/services.py
"""Capa de servicio para la lógica de negocio de Tickets."""

import random
from typing import List

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from participants.models import Participation

from .models import Ticket


def assign_tickets_to_participation(participation: Participation) -> List[Ticket]:
    """
    Asigna y crea los números de ticket para una participación.

    Esta función está diseñada para ser llamada DESPUÉS de que un pago
    ha sido aprobado. Opera dentro de una transacción para garantizar la
    integridad de los datos.

    Args:
        participation: La instancia de Participation cuyo pago fue aprobado.

    Returns:
        Una lista de las instancias de Ticket recién creadas.

    Raises:
        ValueError: Si la participación ya tiene tickets asignados.
    """
    raffle = participation.raffle
    if participation.tickets.exists():
        raise ValueError(
            _(f"Participation {participation.id} already has tickets assigned.")
        )

    # --- Algoritmo Optimizado para Asignación de Tickets ---
    # 1. Obtenemos todos los números ya asignados en esta rifa.
    #    Usar values_list con flat=True es muy eficiente.
    existing_ticket_numbers = set(
        Ticket.objects.filter(raffle=raffle).values_list("ticket_number", flat=True)
    )

    # 2. Generamos una lista de todos los números posibles para la rifa.
    all_possible_numbers = range(0, raffle.total_tickets)

    # 3. Calculamos los números disponibles usando diferencia de conjuntos (muy rápido).
    available_numbers = [
        n for n in all_possible_numbers if n not in existing_ticket_numbers
    ]

    # 4. Verificamos si hay suficientes números disponibles.
    if len(available_numbers) < participation.ticket_count:
        # Esto no debería pasar en un flujo normal, pero es una salvaguarda.
        raise ValueError(
            _(
                f"Not enough available tickets in raffle {raffle.id} "
                f"to assign {participation.ticket_count} tickets."
            )
        )

    # 5. Seleccionamos una muestra aleatoria de los números disponibles.
    chosen_numbers = random.sample(available_numbers, participation.ticket_count)

    # 6. Creamos los objetos Ticket en lote (bulk_create para máximo rendimiento).
    tickets_to_create = [
        Ticket(
            raffle=raffle,
            participation=participation,
            ticket_number=number,
        )
        for number in chosen_numbers
    ]

    # La transacción garantiza que o todos los tickets se crean, o ninguno.
    with transaction.atomic():
        created_tickets = Ticket.objects.bulk_create(tickets_to_create)

    return created_tickets


@transaction.atomic
def revoke_tickets_from_participation(participation: Participation) -> int:
    """
    Elimina todos los tickets asociados a una participación.

    Esta función está diseñada para ser llamada cuando un pago previamente
    aprobado es revertido (cambiado a Pendiente o Rechazado).

    Args:
        participation: La instancia de Participation cuyos tickets serán revocados.

    Returns:
        El número de tickets que fueron eliminados.
    """
    # Usamos select_for_update en la participación para prevenir condiciones
    # de carrera si alguien más intenta operar sobre ella al mismo tiempo.
    participation_to_lock = Participation.objects.select_for_update().get(
        pk=participation.id
    )

    # Eliminamos los tickets y obtenemos la cuenta de objetos borrados.
    deleted_count, _ = participation_to_lock.tickets.all().delete()

    return deleted_count
