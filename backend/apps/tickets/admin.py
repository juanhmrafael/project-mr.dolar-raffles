# backend/apps/tickets/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """
    Panel de administración para el modelo Ticket.

    Permite la búsqueda y filtrado de tickets vendidos, proporcionando
    una herramienta esencial para la auditoría y la consulta de números.
    """

    list_display = (
        "ticket_number_formatted",
        "raffle",
        "participant_info",
        "assigned_at",
    )
    list_filter = ("raffle__title",)
    search_fields = (
        "ticket_number",
        "participation__full_name",
        "participation__identification_number",
        "participation__email",
        "participation__phone",
    )
    autocomplete_fields = ("raffle", "participation")
    list_select_related = ("raffle", "participation")  # Optimización de queries
    ordering = ("-assigned_at",)

    def get_queryset(self, request):
        """
        Optimiza la consulta para evitar N+1 queries.
        """
        return super().get_queryset(request).select_related("raffle", "participation")

    @admin.display(description=_("Ticket Number"), ordering="ticket_number")
    def ticket_number_formatted(self, obj: Ticket) -> str:
        """
        Formatea el número de ticket con ceros a la izquierda.
        """
        padding = obj.raffle.ticket_number_digits
        return str(obj.ticket_number).zfill(padding)

    @admin.display(description=_("Participant"))
    def participant_info(self, obj: Ticket) -> str:
        """
        Muestra el nombre del participante.
        """
        return obj.participation.full_name

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Cuando se está editando un objeto existente
            return [field.name for field in self.model._meta.fields]
        return self.readonly_fields

    def has_add_permission(self, request):
        """
        Deshabilita la creación de nuevos objetos.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Deshabilita la edición de objetos existentes.
        Los usuarios aún podrán ver el formulario de cambio, pero no podrán guardar.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Deshabilita la eliminación de objetos.
        """
        return False

    # Opcional: Para eliminar la acción de "eliminar seleccionados" en la vista de lista
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions