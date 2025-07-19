# backend/apps/participants/views.py
from adrf.views import APIView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .exceptions import NotEnoughTicketsError, RaffleNotAvailableError
from .serializers import (
    ParticipationCreatedSerializer,
    ParticipationCreateSerializer,
    ParticipationStatusSerializer,
    TicketLookupSerializer,
)
from .services_async import (
    create_participation_and_reserve_tickets,
    find_participations_in_raffle,
)


@method_decorator(ratelimit(key="ip", rate="6/m", block=True), name="post")
class CreateParticipationAPIView(APIView):
    """
    Endpoint para que un usuario cree una participación en una rifa.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    async def post(self, request, *args, **kwargs):
        """
        Maneja la creación de una nueva participación.
        """
        serializer = ParticipationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # PASO 2: Ejecución de la validación asíncrona y obtención de los datos.
            # Aquí se ejecuta nuestro 'async def validate'.
            validated_data = await serializer.validated_data

        except serializers.ValidationError as exc:
            # Si 'async def validate' lanza un error, lo capturamos aquí.
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        try:
            participation = await create_participation_and_reserve_tickets(
                **validated_data
            )
        except RaffleNotAvailableError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NotEnoughTicketsError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        # Devolvemos una respuesta ligera con los datos necesarios para el siguiente paso
        response_serializer = ParticipationCreatedSerializer(participation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class TicketLookupAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @method_decorator(ratelimit(key="ip", rate="10/m", block=True))
    async def post(self, request, *args, **kwargs):
        input_serializer = TicketLookupSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        participations = await find_participations_in_raffle(
            **input_serializer.validated_data
        )

        output_serializer = ParticipationStatusSerializer(participations, many=True)
        return Response(output_serializer.data)
