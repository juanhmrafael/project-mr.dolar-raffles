# backend/apps/raffles/views.py
from datetime import date

from adrf.views import APIView
from currencies.services_async import get_exchange_rate_for_date

# from django.core.cache import cache
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit
from participants.services_async import get_raffle_stats
from payments.models import PaymentMethod, Bank
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

    @method_decorator(ratelimit(key="ip", rate="30/m", block=True))
    async def get(self, request, slug, *args, **kwargs):
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



        # --- OPTIMIZACIÓN DE DATOS DE BANCOS (LÓGICA CORREGIDA) ---
        payment_methods = raffle.available_payment_methods.all()

        # 1. ✅ RECOLECTAR CÓDIGOS de banco (no IDs).
        bank_codes = {
            pm.details.get("bank")
            for pm in payment_methods
            if pm.method_type in ("TRANSFERENCIA", "PAGO_MOVIL")
            and pm.details.get("bank")
        }

        # 2. ✅ CONSULTAR por código y crear el mapa por código.
        bank_map_by_code = {}
        if bank_codes:
            # Esta consulta ahora es súper rápida gracias al db_index=True
            banks_data = Bank.objects.filter(code__in=bank_codes).values("code", "name")
            # El mapa ahora se construye con el código del banco como clave.
            bank_map_by_code = {bank["code"]: bank async for bank in banks_data}
            
        # ✅ PASO CLAVE: Obtener la tasa de cambio ANTES de serializar.
        rate_obj = None
        if raffle.status == Raffle.Status.IN_PROGRESS:
            # Esta función debe estar optimizada con caché.
            rate_obj = await get_exchange_rate_for_date(date.today())

        # 3. ✅ PASAR el mapa correcto al contexto del serializer.
        context = {
            "rate_obj": rate_obj,
            "bank_map_by_code": bank_map_by_code,
        }
        serializer = PublicRaffleDetailSerializer(raffle, context=context)

        # Nota: La lógica de caché de respuesta completa se ha omitido como se recomendó.
        return Response(serializer.data)
