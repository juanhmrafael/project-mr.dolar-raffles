# backend/apps/payments/views.py

from datetime import datetime

from adrf.views import APIView
from asgiref.sync import sync_to_async
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit
from participants.models import Participation
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from ..models import PaymentMethod
from .exceptions import (
    DuplicatePaymentError,
    ExchangeRateUnavailableError,
    InvalidPaymentMethodError,
)
from .serializers_async import (
    PublicPaymentCreateSerializer,
)
from .serializers_sync import PaymentMethodLightSerializer
from .services_async import (
    create_payment_for_participation_async,
)
from .services_sync import calculate_payment_amount


class PaymentMethodsForParticipationAPIView(APIView):
    """
    API View para obtener los métodos de pago disponibles
    para una participación específica.
    """

    permission_classes = [IsAdminUser]
    authentication_classes = [SessionAuthentication]

    async def get(self, request, participation_id, *args, **kwargs):
        """
        Devuelve una lista de métodos de pago válidos para la rifa
        asociada a la participación.

        Args:
            request: La petición HTTP.
            participation_id: El ID de la Participation seleccionada.

        Returns:
            Response: Una respuesta JSON con la lista de métodos de pago.
        """
        try:
            # ✅ Usamos el ORM asíncrono
            participation = await Participation.objects.select_related("raffle").aget(
                pk=participation_id
            )

            # ✅ Usamos una comprensión de lista asíncrona
            available_methods = [
                method
                async for method in participation.raffle.available_payment_methods.filter(
                    is_active=True
                )
            ]
            # ✅ Usamos el serializer SÍNCRONO. Esto es seguro porque la serialización
            # de estos datos simples no realiza I/O. DRF/adrf lo maneja correctamente.
            serializer = PaymentMethodLightSerializer(available_methods, many=True)
            return Response(serializer.data)

        except Participation.DoesNotExist:
            return Response({"error": "Participation not found"}, status=404)


class CalculatePaymentAmountAPIView(APIView):
    """
    API View para calcular el monto a pagar en tiempo real.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    async def get(self, request, *args, **kwargs):
        """
        Calcula el monto a pagar basado en la participación,
        el método de pago y la fecha.

        Query Params:
            participation_id (int): ID de la participación.
            payment_method_id (int): ID del método de pago.
            payment_date (str): Fecha del pago en formato YYYY-MM-DD.
        """
        participation_id = request.query_params.get("participation_id")
        payment_method_id = request.query_params.get("payment_method_id")
        payment_date_str = request.query_params.get("payment_date")

        if not all([participation_id, payment_method_id, payment_date_str]):
            return Response({"error": _("Missing required parameters")}, status=400)

        try:
            participation = await Participation.objects.aget(pk=participation_id)
            payment_method = await PaymentMethod.objects.aget(pk=payment_method_id)
            payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()

            amount, currency, rate = await sync_to_async(
                calculate_payment_amount, thread_sensitive=True
            )(participation, payment_method, payment_date)

            return Response(
                {
                    "amount_to_pay": f"{amount:.2f}",
                    "currency": currency,
                    "exchange_rate_applied": f"{rate:.4f}" if rate else None,
                }
            )
        except (Participation.DoesNotExist, PaymentMethod.DoesNotExist):
            return Response({"error": _("Invalid ID provided")}, status=404)
        except (InvalidPaymentMethodError, ExchangeRateUnavailableError) as e:
            return Response({"error": str(e)}, status=400)
        except ValueError:
            return Response(
                {"error": _("Invalid date format. Use YYYY-MM-DD.")}, status=400
            )


class PublicPaymentCreateAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    async def post(self, request, *args, **kwargs):
        serializer = PublicPaymentCreateSerializer(data=request.data)

        # Usamos el patrón de validación en dos pasos de adrf
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            validated_data = await serializer.validated_data
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        try:
            await create_payment_for_participation_async(**validated_data)
            return Response(
                {"status": _("Payment reported successfully. Awaiting verification.")},
                status=status.HTTP_201_CREATED,
            )
        # Capturamos explícitamente el error de validación del servicio síncrono
        except DuplicatePaymentError:
            return Response(
                {
                    "error": _(
                        "A payment with these exact details has already been reported."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        except (InvalidPaymentMethodError, ExchangeRateUnavailableError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
