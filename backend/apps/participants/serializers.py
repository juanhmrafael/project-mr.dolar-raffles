# backend/apps/participants/serializers.py
from adrf.serializers import ModelSerializer as AsyncModelSerializer
from adrf.serializers import Serializer as AsyncSerializer
from django.utils.translation import gettext_lazy as _
from raffles.models import Raffle
from rest_framework import serializers
from utils.validators import (
    validate_full_name,
    validate_natural_person_id,
    validate_venezuelan_phone,
)

from .models import Participation
from tickets.models import Ticket

class ParticipationCreateSerializer(AsyncModelSerializer):
    """
    Serializer para validar y crear una nueva participación.
    """

    raffle_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Participation
        fields = [
            "raffle_id",
            "full_name",
            "phone",
            "email",
            "identification_number",
            "ticket_count",
        ]
        # Aplicamos los validadores que ya tenemos
        extra_kwargs = {
            "full_name": {"validators": [validate_full_name]},
            "phone": {"validators": [validate_venezuelan_phone]},
            "identification_number": {"validators": [validate_natural_person_id]},
        }

    def validate_ticket_count(self, value: int) -> int:
        """Valida que el número de tickets sea positivo."""
        if value <= 0:
            raise serializers.ValidationError(
                _("You must purchase at least one ticket.")
            )
        # La validación contra el mínimo de la rifa se hace en el siguiente paso
        return value

    async def validate(self, data):
        """Validación a nivel de objeto para reglas de negocio complejas."""
        raffle_id = data["raffle_id"]
        try:
            raffle = await Raffle.objects.aget(pk=raffle_id)
        except Raffle.DoesNotExist:
            raise serializers.ValidationError({"raffle_id": _("Raffle not found.")})

        if not raffle.is_active or raffle.status != Raffle.Status.IN_PROGRESS:
            raise serializers.ValidationError(
                {"raffle_id": _("This raffle is not available for participation.")}
            )

        if data["ticket_count"] < raffle.min_ticket_purchase:
            raise serializers.ValidationError(
                {
                    "ticket_count": _(
                        "The minimum purchase for this raffle is %(min_purchase)s tickets."
                    )
                    % {"min_purchase": raffle.min_ticket_purchase}
                }
            )

        return data


class ParticipationCreatedSerializer(AsyncModelSerializer):
    """
    Serializer para la respuesta después de crear una participación.
    Expone solo lo necesario para el frontend.
    """

    class Meta:
        model = Participation
        fields = ["id", "ticket_count", "created_at"]


class TicketLookupSerializer(AsyncSerializer):  # ✅ Hereda de adrf
    """Serializer para validar la entrada de la consulta de tickets."""
    raffle_id = serializers.IntegerField()
    identification_number = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.EmailField()


class TicketSerializer(AsyncModelSerializer):  # ✅ Hereda de adrf
    class Meta:
        model = Ticket
        fields = ["ticket_number", "assigned_at"]


class ParticipationStatusSerializer(AsyncModelSerializer):  # ✅ Hereda de adrf
    """Serializer para mostrar el estado completo de una participación."""

    payment_status = serializers.CharField(
        source="payment.get_status_display", default=_("Pending Payment Report")
    )
    tickets = TicketSerializer(many=True, read_only=True)
    raffle_title = serializers.CharField(source="raffle.title")

    class Meta:
        model = Participation
        fields = [
            "raffle_title",
            "full_name",
            "ticket_count",
            "payment_status",
            "tickets",
        ]
