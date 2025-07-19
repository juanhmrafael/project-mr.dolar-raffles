# backend/apps/payments/services.py
"""
Capa de servicio para la lógica de negocio de Pagos.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Tuple

from asgiref.sync import sync_to_async
from currencies.services_async import get_exchange_rate_for_date
from django.utils.translation import gettext_lazy as _
from participants.models import Participation
from utils.enums import CurrencyChoices

from payments.models import PaymentMethod

from ..models import Payment
from .exceptions import (
    ExchangeRateUnavailableError,
    InvalidPaymentMethodError,
    PaymentCalculationError,
)
from .services_sync import create_payment_sync


async def calculate_payment_amount(
    participation: Participation,
    payment_method: PaymentMethod,
    payment_date: date,
) -> Tuple[Decimal, str, Optional[Decimal]]:
    """
    Calcula el monto total a pagar para una participación según el método de pago.

    Implementa la lógica de conversión de moneda basada en la moneda de la rifa
    y la moneda del método de pago.

    Args:
        participation: La instancia de Participation.
        payment_method: El método de pago que el usuario usará.
        payment_date: La fecha del pago, para determinar la tasa de cambio.

    Returns:
        Una tupla con: (monto_a_pagar, código_de_moneda, tasa_aplicada | None).

    Raises:
        InvalidPaymentMethodError: Si el método de pago no es válido para la rifa.
        ExchangeRateUnavailableError: Si se necesita una tasa y no está disponible.
    """
    raffle = participation.raffle

    # 1. Validación de Seguridad: ¿Es válido este método de pago?
    if not await raffle.available_payment_methods.filter(
        pk=payment_method.pk
    ).aexists():
        raise InvalidPaymentMethodError(
            _(
                _("Payment method '%(method_name)s' is not available for this raffle.")
                % {"method_name": payment_method.name}
            )
        )

    base_amount = raffle.ticket_price * participation.ticket_count
    raffle_currency = raffle.currency
    payment_currency = payment_method.currency
    exchange_rate = None

    # 2. Lógica de Cálculo basada en los 4 escenarios
    if raffle_currency == payment_currency:
        # Escenario 1: Rifa USD -> Pago USD (Zelle)
        # Escenario 2: Rifa VEF -> Pago VEF (Pago Móvil)
        # No se necesita conversión.
        amount_to_pay = base_amount
    else:
        # Se necesita conversión, por lo tanto, la tasa es obligatoria.
        rate_obj = await get_exchange_rate_for_date(payment_date)
        if not rate_obj:
            raise ExchangeRateUnavailableError(
                _("No exchange rate available for the date %(date)s.")
                % {"date": payment_date}
            )
        exchange_rate = rate_obj.rate

        if (
            raffle_currency == CurrencyChoices.USD
            and payment_currency == CurrencyChoices.VEF
        ):
            # Escenario 3: Rifa USD -> Pago VEF (Pago Móvil)
            # Convertir el monto base (en USD) a VEF.
            amount_to_pay = (base_amount * exchange_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        elif (
            raffle_currency == CurrencyChoices.VEF
            and payment_currency == CurrencyChoices.USD
        ):
            # Escenario 4: Rifa VEF -> Pago USD (Zelle)
            # Convertir el monto base (en VEF) a USD.
            amount_to_pay = (base_amount / exchange_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            # Caso de seguridad: combinación de monedas no esperada.
            raise PaymentCalculationError(_("Unexpected currency combination."))

    return amount_to_pay, payment_currency, exchange_rate


async def create_payment_for_participation_async(
    participation_id: int,
    payment_method_id: int,
    payment_date: date,
    transaction_details: dict,
) -> Payment:
    """
    Wrapper asíncrono para crear un registro de Pago.
    """
    payment = await sync_to_async(create_payment_sync, thread_sensitive=True)(
        participation_id=participation_id,
        payment_method_id=payment_method_id,
        payment_date=payment_date,
        transaction_details=transaction_details,
    )
    return payment
