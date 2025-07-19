# backend/apps/raffles/serializers.py
from typing import Dict, Optional

from adrf.serializers import ModelSerializer as AsyncModelSerializer
from adrf.serializers import Serializer as AsyncSerializer
from payments.payment.serializers_async import PublicPaymentMethodDetailSerializer
from rest_framework import serializers

from .models import Prize, Raffle

# PublicPrizeSerializer no cambia
class PublicPrizeSerializer(AsyncModelSerializer):
    """Serializer para exponer los datos públicos de un premio."""

    class Meta:
        model = Prize
        fields = ["level_title", "name", "display_order"]


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
        ]
