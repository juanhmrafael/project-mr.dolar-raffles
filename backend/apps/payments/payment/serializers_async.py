# backend/apps/payments/serializers.py
"""Serializers para la app de pagos."""

from adrf.serializers import ModelSerializer as AsyncModelSerializer
from adrf.serializers import Serializer as AsyncSerializer
from django.utils.translation import gettext_lazy as _
from participants.models import Participation
from rest_framework import serializers

from ..models import PaymentMethod
from typing import Optional

class PublicPaymentMethodDetailSerializer(AsyncModelSerializer):
    """
    Serializer para exponer los detalles PÚBLICOS de un método de pago.
    Crucial para que el usuario sepa a dónde transferir.
    """
    bank_details_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        # Exponemos los campos necesarios para que el frontend construya la UI
        fields = [
            "id",
            "name",
            "method_type",
            "currency",
            "details",
            "bank_details_display",
        ]
        read_only_fields = fields

    def get_bank_details_display(self, obj: PaymentMethod) -> Optional[str]:
        """
        Genera una cadena legible para los detalles bancarios si el método
        es una Transferencia o un Pago Móvil, buscando por CÓDIGO de banco.
        """
        if obj.method_type not in ("TRANSFERENCIA", "PAGO_MOVIL"):
            return None

        # ✅ CORREGIDO: Buscamos la clave 'bank' que contiene el código.
        bank_code = obj.details.get("bank")
        if not bank_code:
            return None

        # ✅ CORREGIDO: Buscamos en el mapa usando el código como clave.
        bank_map = self.context.get("bank_map_by_code", {})
        bank_data = bank_map.get(bank_code)

        if bank_data:
            # El nombre ya está en el mapa, no se necesita el código.
            return f"({bank_code}) - {bank_data['name']}"

        return None
    
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
