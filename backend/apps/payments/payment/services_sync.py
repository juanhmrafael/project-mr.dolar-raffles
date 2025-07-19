# backend/apps/payments/services.py
"""
Capa de servicio para la lógica de negocio de Pagos.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Tuple

from currencies.services_sync import get_exchange_rate_for_date
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from participants.models import Participation
from tickets.services import (
    assign_tickets_to_participation,
    revoke_tickets_from_participation,
)
from utils.enums import CurrencyChoices

from ..models import Payment, PaymentMethod
from .exceptions import (
    ExchangeRateUnavailableError,
    InvalidPaymentMethodError,
    PaymentCalculationError,
    DuplicatePaymentError
)


def calculate_payment_amount(
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
    if not raffle.available_payment_methods.filter(pk=payment_method.pk).exists():
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
        rate_obj = get_exchange_rate_for_date(payment_date)
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


@transaction.atomic
def create_payment_for_participation(
    participation: Participation,
    payment_method: PaymentMethod,
    payment_date: date,
    transaction_details: dict,
) -> Payment:
    """
    Servicio de alto nivel para crear un registro de Pago completo.

    Orquesta el cálculo y la creación del objeto Payment dentro de una
    transacción atómica para garantizar la integridad de los datos.

    Args:
        participation: La instancia de Participation.
        payment_method: El método de pago utilizado.
        payment_date: La fecha del pago.
        transaction_details: Un dict con los detalles (ej: {'reference': '123'}).

    Returns:
        La instancia del objeto Payment recién creado.
    """
    amount, currency, rate = calculate_payment_amount(
        participation, payment_method, payment_date
    )

    # El modelo Payment no tiene un campo para la moneda, ya que se deriva
    # del método de pago. La validación está implícita.

    payment = Payment.objects.create(
        participation=participation,
        payment_method_used=payment_method,
        transaction_details=transaction_details,
        payment_date=payment_date,
        amount_to_pay=amount,  # El monto calculado en la moneda del pago
        exchange_rate_applied=rate,
        # ✅ SNAPSHOT: Congelamos los datos para auditoría
        ticket_price_at_creation=participation.raffle.ticket_price,
        ticket_count_at_creation=participation.ticket_count,
    )
    return payment


@transaction.atomic
def approve_payment(payment: Payment, verified_by: get_user_model) -> Payment:
    """
    Aprueba un pago, asigna los tickets correspondientes y registra la auditoría.

    Esta operación es atómica e idempotente. Si se llama varias veces para el
    mismo pago, solo se ejecutará la primera vez.

    Args:
        payment: La instancia del Pago a aprobar.
        verified_by: El usuario administrador que realiza la aprobación.

    Returns:
        La instancia del Pago actualizada.

    Raises:
        ValueError: Si el pago no está en estado 'PENDING'.
    """
    # Bloqueamos la fila del pago para prevenir condiciones de carrera.
    payment_to_approve = Payment.objects.select_for_update().get(pk=payment.pk)

    # ✅ CORRECCIÓN: La verdadera condición de idempotencia es si ya existen tickets.
    if payment_to_approve.participation.tickets.exists():
        # Ya tiene tickets, no hay nada que hacer. Actualizamos la auditoría y salimos.
        payment_to_approve.verified_by = verified_by
        payment_to_approve.verified_at = timezone.now()
        payment_to_approve.status = "APPROVED"  # Aseguramos el estado
        payment_to_approve.save(update_fields=["verified_by", "verified_at", "status"])
        return payment_to_approve

    # Si no tiene tickets, los asignamos.
    assign_tickets_to_participation(payment_to_approve.participation)

    # Actualizamos el estado del pago y los campos de auditoría.
    payment_to_approve.status = "APPROVED"
    payment_to_approve.verified_by = verified_by
    payment_to_approve.verified_at = timezone.now()
    payment_to_approve.save()  # Guardamos todos los campos actualizados.

    return payment_to_approve


@transaction.atomic
def revert_approved_payment(payment: Payment, reverted_by: get_user_model) -> Payment:
    """
    Revierte un pago previamente aprobado, eliminando los tickets asociados.

    Args:
        payment: La instancia del Pago a revertir.
        reverted_by: El usuario administrador que realiza la reversión.

    Returns:
        La instancia del Pago actualizada.

    Raises:
        ValueError: Si el pago no estaba en estado 'APPROVED'.
    """
    payment_to_revert = Payment.objects.select_for_update().get(pk=payment.pk)

    revoke_tickets_from_participation(payment_to_revert.participation)

    return payment_to_revert


@transaction.atomic
def create_payment_sync(
    participation_id: int,
    payment_method_id: int,
    payment_date: date,
    transaction_details: dict,
) -> Payment:
    from django.utils.translation import gettext_lazy as _
    """
    Crea un registro de pago completo dentro de una transacción síncrona y segura.
    """
    participation = Participation.objects.select_for_update().get(pk=participation_id)
    payment_method = PaymentMethod.objects.get(pk=payment_method_id)

    if not participation.raffle.available_payment_methods.filter(
        pk=payment_method.pk
    ).exists():
        raise InvalidPaymentMethodError(
            _("Payment method '%(method_name)s' is not available for this raffle.")
            % {"method_name": payment_method.name}
        )

    amount, _, rate = calculate_payment_amount(
        participation, payment_method, payment_date
    )

    payment = Payment(
        participation=participation,
        payment_method_used=payment_method,
        transaction_details=transaction_details,
        payment_date=payment_date,
        amount_to_pay=amount,
        exchange_rate_applied=rate,
        ticket_price_at_creation=participation.raffle.ticket_price,
        ticket_count_at_creation=participation.ticket_count,
    )

    payment.payment_hash = payment._generate_hash()

    try:
        payment.save()
    except IntegrityError:
        raise DuplicatePaymentError(
            "A payment with these exact details has already been reported."
        )

    return payment
