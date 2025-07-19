# backend/apps/participants/admin.py
"""Configuración del Admin para el modelo Participation."""

from django.contrib import admin, messages
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import Participation
from .tasks import cleanup_expired_participation


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    """Admin para el modelo de Participaciones."""

    list_display = ("full_name", "raffle", "ticket_count", "created_at")
    search_fields = (
        "full_name__icontains",
        "identification_number__icontains",
        "email__icontains",
        "raffle__title__icontains",
    )
    list_filter = ("raffle",)
    list_select_related = ("raffle",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("raffle",)

    class Media:
        js = (
            "assets/js/vendor/inputmask.min.js",
            "assets/js/core/app-masks.js",
            "assets/js/participation.js",
        )

    def save_model(self, request, obj: Participation, form, change: bool):
        """
        Sobrescribe el guardado para encolar la tarea de expiración al crear
        una nueva participación.
        """
        # Primero, guardamos el objeto para que obtenga un ID de base de datos.
        super().save_model(request, obj, form, change)

        # La variable 'change' es True si estamos editando un objeto existente
        # y False si es un objeto nuevo.
        if not change:
            # Si estamos creando una nueva participación...

            # Encolamos la tarea de limpieza para que se ejecute en 5 minutos.
            cleanup_expired_participation.apply_async(
                args=[obj.id],
                countdown=300,  # 300 segundos = 5 minutos
            )

            # Mostramos un mensaje informativo al administrador.
            self.message_user(
                request,
                _(
                    "The participation has been created successfully. It will expire in 5 minutes if a payment is not registered."
                ),
                messages.SUCCESS,
            )

    def get_readonly_fields(
        self, request: HttpRequest, obj: Participation | None = None
    ) -> list[str] | tuple[str]:
        """
        Hace que el campo 'raffle' sea de solo lectura después de que la
        participación ha sido creada.

        Args:
            request: El objeto de la petición HTTP.
            obj: La instancia de Participation que se está editando.
                 Es `None` si se está creando un nuevo objeto.

        Returns:
            Una tupla o lista de nombres de campos que deben ser de solo lectura.
        """
        # Obtenemos la lista base de campos de solo lectura definidos en la clase.
        base_readonly = list(super().get_readonly_fields(request, obj))

        # ✅ LÓGICA PRINCIPAL
        # Si el objeto ya existe (es decir, estamos en la vista de edición, no de creación)...
        if obj:
            # ...añadimos 'raffle' a la lista de campos de solo lectura.
            base_readonly.append("raffle")

        return base_readonly

    def get_search_results(self, request, queryset, search_term):
        """
        Sobrescribe la búsqueda para el autocompletado.

        Si la ruta de la petición contiene '/autocomplete/', significa que la llamada
        proviene de un widget de autocompletado. En ese caso, filtramos para
        excluir las participaciones que ya tienen un pago.

        Esta es una solución simple y robusta que no afecta a la búsqueda
        normal en la vista de lista de participaciones.
        """
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # request.path contiene la ruta de la URL de la petición actual.
        if "/autocomplete/" in request.path:
            queryset = queryset.exclude(payment__isnull=False)

        return queryset, use_distinct

    def has_change_permission(self, request, obj=None):
        return False
