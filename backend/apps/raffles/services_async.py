# backend/apps/raffles/services.py
from typing import Any, Dict, List, Optional

from django.db.models import Prefetch

from .models import Prize, Raffle


async def get_main_page_data() -> Dict[str, Any]:
    """
    Orquesta la obtención de todos los datos necesarios para la página principal.

    Obtiene la rifa principal activa y las 3 rifas secundarias más recientes.

    Returns:
        Un diccionario que contiene los datos de la rifa principal
        y la lista de rifas secundarias.
    """
    main_raffle = await get_active_main_raffle()
    secondary_raffles = await get_secondary_raffles(
        main_raffle_id=main_raffle.id if main_raffle else None, limit=3
    )

    return {
        "main_raffle": main_raffle,
        "secondary_raffles": secondary_raffles,
    }


async def get_active_main_raffle() -> Optional[Raffle]:
    """
    Obtiene la rifa principal activa, optimizada para la API.

    La "rifa principal" se define como la más reciente que está activa y en progreso.
    Precarga los premios para evitar consultas adicionales (N+1).

    Returns:
        Una instancia de Raffle o None si no hay ninguna activa.
    """
    return await (
        Raffle.objects.filter(is_active=True, status=Raffle.Status.IN_PROGRESS)
        .prefetch_related(
            Prefetch("prizes", queryset=Prize.objects.order_by("display_order"))
        )
        .order_by("-start_date")
        .afirst()
    )


async def get_secondary_raffles(
    main_raffle_id: Optional[int], limit: int = 3
) -> List[Raffle]:
    """
    Obtiene una lista de las rifas secundarias más recientes, por fecha de inicio.

    Excluye la rifa principal y puede incluir tanto rifas en progreso como finalizadas.
    Precarga los datos necesarios para renderizar las tarjetas de información.

    Args:
        main_raffle_id: El ID de la rifa principal para excluirla del queryset.
        limit: El número máximo de rifas a devolver.

    Returns:
        Una lista de instancias de Raffle.
    """
    queryset = (
        Raffle.objects.select_related(
            # No necesitamos el 'user' aquí, pero es un buen hábito si lo necesitáramos
        )
        .prefetch_related(
            # Precargamos premios y, a través de ellos, la participación ganadora.
            # Esto es eficiente incluso para rifas no finalizadas, ya que la query
            # simplemente no encontrará relaciones.
            Prefetch(
                "prizes", queryset=Prize.objects.select_related("winner_participation")
            )
        )
        .filter(is_active=True)
        .exclude(status=Raffle.Status.CANCELLED)
        .order_by("-start_date")
    )

    if main_raffle_id:
        queryset = queryset.exclude(pk=main_raffle_id)

    return [raffle async for raffle in queryset[:limit]]
