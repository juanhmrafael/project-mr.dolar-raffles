# backend/apps/currencies/services.py
from datetime import date
from typing import Optional

from .models import ExchangeRate


async def get_exchange_rate_for_date(target_date: date) -> Optional[ExchangeRate]:
    """
    Obtiene la tasa de cambio más reciente que sea igual o anterior a la fecha dada.

    Esta función implementa la regla de negocio clave: para cualquier transacción,
    se debe usar la última tasa de cambio oficial disponible en o antes de la
    fecha de la transacción.

    Args:
        target_date: La fecha para la cual se necesita la tasa de cambio.

    Returns:
        Un objeto ExchangeRate si se encuentra, o None si no hay tasas
        disponibles en o antes de la fecha especificada.
    """
    rate_object = await (
        ExchangeRate.objects.filter(date__lte=target_date).order_by("-date").afirst()
    )
    return rate_object
