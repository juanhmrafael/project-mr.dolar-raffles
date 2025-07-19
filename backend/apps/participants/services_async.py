# backend/apps/participants/services_async.py
import hashlib
from decimal import ROUND_HALF_UP, Decimal

from asgiref.sync import sync_to_async
from django.db import models
from payments.models import Payment
from raffles.models import Raffle

from .models import Participation
from .services_sync import create_participation_sync
from .tasks import cleanup_expired_participation


async def get_unavailable_tickets_count(raffle: Raffle) -> int:
    """
    Calcula el número total de tickets que están "fuera de circulación".

    Esto incluye tickets en participaciones que están reservadas (sin pago),
    pendientes de verificación, o ya aprobadas. La única excepción son
    las participaciones cuyo pago fue explícitamente rechazado.

    Args:
        raffle: La instancia de la rifa.

    Returns:
        El número total de tickets no disponibles.
    """
    aggregation = await raffle.participations.exclude(
        payment__status=Payment.STATUS_CHOICES[2][0]  # Excluye 'REJECTED'
    ).aaggregate(total=models.Sum("ticket_count"))
    return aggregation["total"] or 0


async def create_participation_and_reserve_tickets(
    raffle_id: int,
    full_name: str,
    phone: str,
    email: str,
    identification_number: str,
    ticket_count: int,
) -> Participation:
    """
    Crea una participación, reserva los tickets y programa su expiración.

    Esta operación es atómica y segura contra condiciones de carrera.

    Args:
        raffle_id: ID de la rifa.
        full_name, phone, email, identification_number: Datos del participante.
        ticket_count: Cantidad de tickets a comprar.

    Returns:
        La instancia de la Participation recién creada.

    Raises:
        RaffleNotAvailableError: Si la rifa no está activa o en progreso.
        NotEnoughTicketsError: Si no hay suficientes tickets disponibles.
    """

    participation = await sync_to_async(
        create_participation_sync, thread_sensitive=True
    )(
        raffle_id=raffle_id,
        full_name=full_name,
        phone=phone,
        email=email,
        identification_number=identification_number,
        ticket_count=ticket_count,
    )

    # 4. Programación de la tarea de limpieza en Celery
    cleanup_expired_participation.apply_async(
        args=[participation.id],
        countdown=300,  # 5 minutos
    )

    return participation


async def find_participations_in_raffle(
    raffle_id: int, identification_number: str, phone: str, email: str
) -> list[Participation]:
    """
    Busca participaciones usando la combinación de 3 credenciales hasheadas.
    """

    def _hash_field(data: str) -> str:
        return hashlib.sha256(data.strip().lower().encode("utf-8")).hexdigest()

    id_hash = _hash_field(identification_number)
    phone_hash = _hash_field(phone)
    email_hash = _hash_field(email)

    # La consulta se ejecuta de forma asíncrona
    participations = [
        p
        async for p in Participation.objects.filter(
            raffle_id=raffle_id,
            identification_number_hash=id_hash,
            phone_hash=phone_hash,
            email_hash=email_hash,
        )
        .select_related("raffle", "payment")
        .prefetch_related("tickets")
        .order_by("-created_at")
    ]
    return participations


async def get_raffle_stats(raffle: Raffle) -> dict:
    """
    Calcula TODAS las estadísticas dinámicas para una rifa dada.
    Devuelve el porcentaje con dos decimales de precisión.
    """
    if raffle.status != Raffle.Status.IN_PROGRESS:
        return {"tickets_available": 0, "tickets_progress_percentage": 100}

    # Hacemos las dos consultas de conteo concurrentemente
    unavailable_count = await get_unavailable_tickets_count(raffle)
    available = raffle.total_tickets - unavailable_count

    percentage = Decimal("0.00")
    if raffle.total_tickets > 0:
        raw_percentage = (
            Decimal(unavailable_count) / Decimal(raffle.total_tickets)
        ) * 100

        # Redondeamos a 2 decimales, el estándar para porcentajes.
        percentage = raw_percentage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "tickets_available": max(0, available),
        "tickets_progress_percentage": f"{percentage:.2f}",
    }
