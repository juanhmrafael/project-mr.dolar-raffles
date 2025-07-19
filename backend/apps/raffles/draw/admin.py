from django.contrib import admin
from rangefilter.filters import DateRangeFilter
from simple_history.admin import SimpleHistoryAdmin

from ..models import Draw


class DrawInline(admin.TabularInline):
    """
    Permite crear y editar los Sorteos (Draws) directamente desde la
    vista de un Premio (Prize). Mejora drásticamente el flujo de trabajo.
    """

    model = Draw
    extra = 1  # Muestra 1 formulario vacío para añadir un nuevo sorteo.
    fields = ("lottery_name", "draw_time", "status", "winning_number")
    readonly_fields = ("status",)  # El estado se gestiona por lógica de negocio.


class DrawAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    """
    Admin para el modelo Draw.
    Permite registrar los resultados de los sorteos externos.
    """

    list_display = ("__str__", "prize", "status", "winning_number")
    list_filter = ("status", ("draw_time", DateRangeFilter), "prize__raffle__title")
    search_fields = ("prize__name", "prize__raffle__title")

    # El campo clave que el admin modificará.
    fields = (
        "prize",
        "lottery_name",
        "draw_time",
        "winning_number",
        "status",
    )
    autocomplete_fields = ["prize"]

    readonly_fields = ("status",)  # El estado es manejado por la lógica de negocio.```
