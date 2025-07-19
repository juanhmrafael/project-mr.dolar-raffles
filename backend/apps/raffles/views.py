# backend/apps/raffles/views.py
from adrf.views import APIView
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit
from participants.services_async import get_raffle_stats
from payments.models import PaymentMethod
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Raffle
from .serializers import MainPageDataSerializer, PublicRaffleDetailSerializer
from .services_async import get_main_page_data


class MainPageAPIView(APIView):
    """
    API para servir todos los datos necesarios para la página principal.

    Combina la información de la rifa principal activa y las rifas anteriores
    en una única respuesta optimizada y cacheada.
    """

    permission_classes = [AllowAny]  # API pública, no requiere autenticación
    authentication_classes = []
    CACHE_KEY = "main_page_data_static"
    CACHE_TIMEOUT = 60 * 15  # 5 minutos

    @method_decorator(ratelimit(key="ip", rate="30/m", block=True))
    async def get(self, request, *args, **kwargs):
        """
        Maneja las peticiones GET, aplicando caché y limitación de tasa.
        """
        # cached_data = await cache.aget(self.CACHE_KEY)
        # if cached_data:
        #     return Response(cached_data)

        data = await get_main_page_data()
        serializer = MainPageDataSerializer(data)

        # Guardamos el resultado serializado en caché
        response_data = serializer.data
        # await cache.aset(self.CACHE_KEY, response_data, self.CACHE_TIMEOUT)

        return Response(response_data)


class RaffleStatsAPIView(APIView):
    """
    API NO CACHEADA para obtener las estadísticas dinámicas de CUALQUIER rifa.
    Reutilizable para la página principal y la de detalles.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @method_decorator(ratelimit(key="ip", rate="60/m", block=True))
    async def get(self, request, slug, *args, **kwargs):
        try:
            raffle = await Raffle.objects.aget(slug=slug)
        except Raffle.DoesNotExist:
            return Response(
                {"error": _("Raffle not found")}, status=status.HTTP_404_NOT_FOUND
            )

        stats = await get_raffle_stats(raffle)
        return Response(stats)

class PublicRaffleDetailAPIView(APIView):
    """
    API para obtener los detalles públicos y completos de una rifa.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    CACHE_PREFIX = "raffle_detail_"
    CACHE_TIMEOUT = 60 * 15  # 15 minutos

    @method_decorator(ratelimit(key="ip", rate="30/m", block=True))
    async def get(self, request, slug, *args, **kwargs):
        cache_key = f"{self.CACHE_PREFIX}{slug}"
        cached_data = await cache.aget(cache_key)
        if cached_data:
            return Response(cached_data)

        try:
            # Obtenemos la rifa y precargamos todo lo necesario
            raffle = await Raffle.objects.prefetch_related(
                "prizes",
                Prefetch(
                    "available_payment_methods",
                    queryset=PaymentMethod.objects.filter(is_active=True),
                ),
            ).aget(slug=slug, is_active=True)

            # No mostramos rifas canceladas al público
            if raffle.status == Raffle.Status.CANCELLED:
                return Response(
                    {"error": _("Raffle not found")}, status=status.HTTP_404_NOT_FOUND
                )

        except Raffle.DoesNotExist:
            return Response(
                {"error": _("Raffle not found")}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = PublicRaffleDetailSerializer(raffle)
        await cache.aset(cache_key, serializer.data, self.CACHE_TIMEOUT)

        return Response(serializer.data)

