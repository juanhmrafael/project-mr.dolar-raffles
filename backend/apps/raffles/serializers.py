# backend/apps/raffles/serializers.py
from typing import Dict, Optional

from adrf.serializers import ModelSerializer as AsyncModelSerializer
from adrf.serializers import Serializer as AsyncSerializer
from payments.payment.serializers_async import PublicPaymentMethodDetailSerializer
from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from .models import Prize, Raffle
from babel.dates import format_date

# PublicPrizeSerializer no cambia
class PublicPrizeSerializer(AsyncModelSerializer):
    """Serializer para exponer los datos públicos de un premio."""

    winner_name = serializers.CharField(
        source="winner_participation.full_name", read_only=True, allow_null=True
    )

    class Meta:
        model = Prize
        fields = [
            "level_title",
            "name",
            "display_order",
            "description",
            "image",
            # Campos para el ganador.
            "delivered_image",
            "winner_name",
            "winner_ticket_number",
            "delivered_at",
        ]


# MainRaffleSerializer no cambia
class MainRaffleSerializer(AsyncModelSerializer):
    """Serializer para la rifa principal destacada en la página de inicio."""

    prizes = PublicPrizeSerializer(many=True, read_only=True)

    class Meta:
        model = Raffle
        fields = [
            "id",
            "title",
            "slug",
            "promotional_message",
            "image",
            "end_date",
            "prizes",
        ]


class RaffleCardSerializer(AsyncModelSerializer):
    """
    Serializer para las tarjetas de rifa (tanto activas como finalizadas).
    """

    winner_summary = serializers.SerializerMethodField()
    # Expone el valor legible del estado (ej: "In Progress", "Finished")
    status_display = serializers.CharField(source="get_status_display")

    class Meta:
        model = Raffle
        fields = [
            "id",
            "title",
            "slug",
            "image",
            "end_date",
            "status",
            "status_display",
            "winner_summary",
        ]

    def get_winner_summary(self, obj: Raffle) -> Optional[Dict[str, any]]:
        """
        Genera un resumen del ganador SOLO si la rifa está finalizada.
        Si no, devuelve None.

        Args:
            obj: La instancia de la Rifa.

        Returns:
            Un diccionario con datos del ganador o None.
        """
        if obj.status != Raffle.Status.FINISHED:
            return None

        all_prizes = obj.prizes.all()

        main_winner_prize = next(
            (p for p in all_prizes if p.winner_participation and p.display_order == 1),
            None,
        )

        if not main_winner_prize:
            return {
                "main_winner_name": "Sorteo Finalizado",
                "prize_won": "Sin ganador principal",
                "other_winners_count": 0,
            }

        other_winners_count = sum(
            1
            for p in all_prizes
            if p.winner_participation and p.pk != main_winner_prize.pk
        )

        return {
            "main_winner_name": main_winner_prize.winner_participation.full_name,
            "prize_won": main_winner_prize.name,
            "other_winners_count": other_winners_count,
        }


class MainPageDataSerializer(AsyncSerializer):
    """Serializer raíz que estructura toda la respuesta para la página principal."""

    main_raffle = MainRaffleSerializer(read_only=True, allow_null=True)
    # Cambiamos el nombre para mayor claridad
    secondary_raffles = RaffleCardSerializer(many=True, read_only=True)


class PublicRaffleDetailSerializer(AsyncModelSerializer):
    """
    Serializer para exponer los detalles PÚBLICOS y ESTÁTICOS de una rifa.
    Esta respuesta SÍ se puede cachear de forma segura.
    """

    prizes = PublicPrizeSerializer(many=True, read_only=True)
    # Usamos el nuevo serializer que incluye los detalles de la cuenta
    available_payment_methods = PublicPaymentMethodDetailSerializer(
        many=True, read_only=True
    )
    status_display = serializers.CharField(source="get_status_display")

    applied_rate_date = serializers.SerializerMethodField()
    vef_per_usd_price = serializers.SerializerMethodField()
    unit_price_per_currency = serializers.SerializerMethodField()
    
    class Meta:
        model = Raffle
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "image",
            "currency",
            "ticket_price",
            "min_ticket_purchase",
            "total_tickets",
            "status",
            "status_display",
            "start_date",
            "end_date",
            "prizes",
            "available_payment_methods",
            "applied_rate_date",
            "vef_per_usd_price",
            "unit_price_per_currency",
        ]

    def _get_rate_object_from_context(self):
        """Helper para obtener la tasa del contexto pasado por la vista."""
        return self.context.get("rate_obj")

    # --- Implementación de los métodos para los campos dinámicos ---

    def get_applied_rate_date(self, obj: Raffle) -> Optional[str]:
        """Devuelve la fecha de la tasa formateada, solo si la rifa está en progreso."""
        rate_obj = self._get_rate_object_from_context()
        if obj.status == Raffle.Status.IN_PROGRESS and rate_obj:
            return format_date(rate_obj.date, format="full", locale="es").capitalize()
        return None

    def get_vef_per_usd_price(self, obj: Raffle) -> Optional[Decimal]:
        """Devuelve el valor de la tasa, solo si la rifa está en progreso."""
        rate_obj = self._get_rate_object_from_context()
        if obj.status == Raffle.Status.IN_PROGRESS and rate_obj:
            return rate_obj.rate
        return None

    def get_unit_price_per_currency(self, obj: Raffle) -> Optional[dict]:
        """
        Calcula y devuelve los precios unitarios en USD y VEF.
        Solo si la rifa está en progreso.
        """
        if obj.status != Raffle.Status.IN_PROGRESS:
            return None

        rate_obj = self._get_rate_object_from_context()
        if not rate_obj:
            # Si no hay tasa, no podemos calcular, devolvemos null.
            # Podrías querer lanzar un error si la tasa es obligatoria para rifas en progreso.
            return None

        base_price = obj.ticket_price
        rate = rate_obj.rate

        if obj.currency == "USD":
            price_in_usd = base_price
            price_in_vef = (base_price * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        elif obj.currency == "VEF":
            price_in_vef = base_price
            price_in_usd = (base_price / rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            # Combinación no soportada
            return None

        # Usamos el serializer anidado para asegurar el formato correcto.
        price_serializer = UnitPriceSerializer(
            data={"USD": price_in_usd, "VEF": price_in_vef}
        )
        price_serializer.is_valid(raise_exception=True)
        return price_serializer.data
    
class UnitPriceSerializer(serializers.Serializer):
    """
    Representa el precio de un ticket en ambas monedas clave.
    """

    USD = serializers.DecimalField(max_digits=12, decimal_places=4)
    VEF = serializers.DecimalField(max_digits=12, decimal_places=2)
