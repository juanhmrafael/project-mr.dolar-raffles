# backend/apps/payments/serializers.py
"""Serializers para la app de pagos."""

from adrf.serializers import ModelSerializer as AsyncModelSerializer
from adrf.serializers import Serializer as AsyncSerializer
from django.utils.translation import gettext_lazy as _
from participants.models import Participation
from rest_framework import serializers

from ..models import PaymentMethod

class PublicCalculationInputSerializer(AsyncSerializer):
    """Serializer para validar la entrada de la API de cálculo público."""

    raffle_id = serializers.IntegerField()
    payment_method_id = serializers.IntegerField()
    ticket_count = serializers.IntegerField(min_value=1)


class PublicCalculationOutputSerializer(AsyncSerializer):
    """Serializer para formatear la salida de la API de cálculo."""

    amount_to_pay = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    exchange_rate_applied = serializers.DecimalField(
        max_digits=10, decimal_places=4, required=False, allow_null=True
    )


class PublicPaymentMethodDetailSerializer(AsyncModelSerializer):
    """
    Serializer para exponer los detalles PÚBLICOS de un método de pago.
    Crucial para que el usuario sepa a dónde transferir.
    """

    class Meta:
        model = PaymentMethod
        # Exponemos los campos necesarios para que el frontend construya la UI
        fields = ["id", "name", "method_type", "currency", "details"]


class PublicPaymentCreateSerializer(
    AsyncSerializer
):  # ✅ Heredamos del Serializer de adrf
    """
    Serializer para validar la creación de un pago desde la API pública.
    """

    participation_id = serializers.IntegerField()
    payment_method_id = serializers.IntegerField()
    payment_date = serializers.DateField()
    transaction_details = serializers.JSONField()

    # ✅ Usamos 'validate' asíncrono para mantener la consistencia
    async def validate(self, data):
        """Validación asíncrona de los IDs y coherencia."""
        try:
            # Verificamos que la participación exista y aún no tenga un pago.
            participation = await Participation.objects.select_related("payment").aget(
                pk=data["participation_id"]
            )
            # hasattr es seguro aquí porque 'payment' fue precargado con select_related
            if hasattr(participation, "payment") and participation.payment is not None:
                raise serializers.ValidationError(
                    _("This participation already has a payment reported.")
                )
        except Participation.DoesNotExist:
            raise serializers.ValidationError(
                {"participation_id": _("Participation not found.")}
            )

        try:
            payment_method = await PaymentMethod.objects.aget(
                pk=data["payment_method_id"]
            )
            details = data["transaction_details"]

            # Definimos los campos requeridos para cada tipo
            required_fields_map = {
                "PAGO_MOVIL": ("reference",),
                "TRANSFERENCIA": ("reference",),
                "ZELLE": ("reference", "email"),
                "BINANCE": ("reference", "binance_pay_id"),
            }

            required_fields = required_fields_map.get(
                payment_method.method_type, ("reference",)
            )

            missing_fields = [
                field
                for field in required_fields
                if field not in details or not details[field]
            ]
            if missing_fields:
                raise serializers.ValidationError(
                    {
                        "transaction_details": _(
                            "Missing required details for this payment method: %(fields)s"
                        )
                        % {"fields": ", ".join(missing_fields)}
                    }
                )

        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError(
                {"payment_method_id": _("Payment method not found.")}
            )
        return data
