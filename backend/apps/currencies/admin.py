# backend/apps/currencies/admin.py
"""
Configuración del panel de administración para la app 'currencies'.
"""

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilter
from simple_history.admin import SimpleHistoryAdmin
from utils.bcv_scrapers import BCVScraper

from .models import ExchangeRate


@admin.register(ExchangeRate)
class ExchangeRateAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    """
    Admin para el historial de tasas de cambio.
    Permite a un superusuario añadir o corregir una tasa manualmente.
    """

    list_display = ("date", "rate", "source")
    list_filter = ("source", ( "date", DateRangeFilter))
    ordering = ("-date",)
    # Hacer que la fecha sea de solo lectura después de la creación para evitar errores.
    readonly_fields = ("source",)

    def get_readonly_fields(self, request, obj=None):
        """
        La fuente siempre es de solo lectura en la interfaz, ya que es
        gestionada por el sistema. La fecha solo se puede establecer al crear.
        """
        if obj:  # Si el objeto ya existe (edición)
            return ("source", "date")
        return ("source",)  # Si es un objeto nuevo

    def save_model(self, request, obj, form, change):
        """
        Lógica personalizada al guardar. Aquí es donde ocurre la magia.
        'change' es True si se está editando un objeto existente.
        """
        if change:
            # Si el admin está EDITANDO, asumimos que es una corrección manual.
            obj.source = "MANUAL_INPUT"
        else:
            # Si el admin está CREANDO un nuevo registro manualmente.
            obj.source = "MANUAL_INPUT"

        super().save_model(request, obj, form, change)

    def get_urls(self):
        """
        Añade una URL personalizada para nuestra acción de "Obtener Tasa".
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "fetch-current-rate/",
                self.admin_site.admin_view(self.fetch_current_rate),
                name="currencies_exchangerate_fetch_current_rate",
            ),
        ]
        return custom_urls + urls

    def fetch_current_rate(self, request):
        """
        Esta vista es llamada por nuestra acción. Ejecuta el scraper
        y crea o actualiza la tasa de cambio.
        """
        scraper = BCVScraper()
        data = scraper.get_processed_data()

        if data:
            effective_date = data["date"]
            usd_rate = data["rates"]["USD"]

            # Al obtener del scraper, la fuente siempre es 'BCV_SCRAPER'.
            # Usamos get_or_create para no sobreescribir una entrada manual.
            obj, created = ExchangeRate.objects.get_or_create(
                date=effective_date,
                defaults={"rate": usd_rate, "source": "BCV_SCRAPER"},
            )

            if created:
                self.message_user(
                    request,
                    _("Successfully fetched and created rate for %s.") % effective_date,
                    messages.SUCCESS,
                )
            else:
                # Si ya existe, informamos pero no la modificamos para respetar las ediciones manuales.
                self.message_user(
                    request,
                    _("Rate for %s already exists. Source: %s.")
                    % (effective_date, obj.get_source_display()),
                    messages.WARNING,
                )
        else:
            self.message_user(
                request, _("Failed to fetch rate from BCV."), messages.ERROR
            )

        return HttpResponseRedirect("../")

    def changelist_view(self, request, extra_context=None):
        """
        Sobrescribe la vista de la lista para añadir nuestro botón personalizado.
        """
        extra_context = extra_context or {}
        extra_context["show_fetch_button"] = True
        return super().changelist_view(request, extra_context)
