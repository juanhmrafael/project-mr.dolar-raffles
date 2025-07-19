# backend/apps/participants/services_sync.py
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from raffles.models import Raffle

from .exceptions import NotEnoughTicketsError, RaffleNotAvailableError
from .models import Participation


def get_available_tickets_count_sync(raffle: Raffle) -> int:
    """Calcula la disponibilidad de tickets (SÍNCRONO)."""
    if raffle.status != Raffle.Status.IN_PROGRESS:
        return 0

    unavailable_count = (
        raffle.participations.exclude(payment__status="REJECTED").aggregate(
            total=models.Sum("ticket_count")
        )["total"]
        or 0
    )

    available = raffle.total_tickets - unavailable_count
    return max(0, available)


@transaction.atomic
def create_participation_sync(
    raffle_id: int,
    full_name: str,
    phone: str,
    email: str,
    identification_number: str,
    ticket_count: int,
) -> Participation:
    """
    Crea una participación dentro de una transacción síncrona.
    """
    # Usamos el ORM síncrono porque estamos en una función síncrona.
    raffle = Raffle.objects.select_for_update().get(pk=raffle_id)

    if not raffle.is_active or raffle.status != Raffle.Status.IN_PROGRESS:
        raise RaffleNotAvailableError(
            _("This raffle is not available for participation.")
        )

    available_tickets = get_available_tickets_count_sync(raffle)
    if ticket_count > available_tickets:
        raise NotEnoughTicketsError(_("Not enough tickets available."))

    participation = Participation.objects.create(
        raffle=raffle,
        full_name=full_name,
        phone=phone,
        email=email,
        identification_number=identification_number,
        ticket_count=ticket_count,
    )
    return participation
