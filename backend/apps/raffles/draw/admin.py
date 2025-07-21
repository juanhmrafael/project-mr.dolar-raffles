from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilter
from simple_history.admin import SimpleHistoryAdmin

from ..models import Draw
from ..service_sync import DrawProcessingError, process_draw_result, revoke_prize_assignment, RevokePrizeError

class DrawInline(admin.TabularInline):
    model = Draw
    extra = 1
    fields = ("lottery_name", "draw_time", "status", "winning_number")
    readonly_fields = ("status",)


class DrawAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    list_display = ("__str__", "prize", "status", "winning_number")
    list_filter = ("status", ("draw_time", DateRangeFilter), "prize__raffle__title")
    search_fields = ("prize__name", "prize__raffle__title")
    autocomplete_fields = ["prize"]
    actions = ["revoke_draw_and_reschedule"]
    fieldsets = (
        (
            _("Información del Sorteo"),
            {"fields": ("prize", "lottery_name", "draw_time", "status")},
        ),
        (
            _("Procesar Resultado"),
            {
                "description": _(
                    "Para un sorteo 'Programado', introduzca el número ganador aquí y "
                    "haga clic en 'Guardar'. El sistema asignará el premio o lo acumulará "
                    "automáticamente."
                ),
                "fields": ("winning_number",),
            },
        ),
    )

    @admin.action(description=_("Revocar sorteo y programar uno nuevo"))
    def revoke_draw_and_reschedule(self, request, queryset):
        """
        Invoca el servicio central para revocar el premio asociado a los sorteos seleccionados.
        """
        # Filtramos para actuar solo sobre sorteos que están 'COMPLETED'
        valid_draws = queryset.filter(status="COMPLETED")

        if valid_draws.count() < queryset.count():
            self.message_user(
                request,
                _("Acción solo aplicable a sorteos con estado 'Completado'."),
                messages.WARNING,
            )

        revoked_count = 0
        for draw in valid_draws:
            try:
                # La lógica de negocio se aplica al PREMIO, no al sorteo.
                revoke_prize_assignment(draw.prize)
                revoked_count += 1
            except RevokePrizeError as e:
                self.message_user(request, str(e), messages.ERROR)

        if revoked_count > 0:
            self.message_user(
                request,
                _(f"{revoked_count} sorteo(s) han sido revocados y reprogramados."),
                messages.SUCCESS,
            )
            
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ["status"]
        if obj:
            # ✅ DEFINITIVO: Comparamos con el string "SCHEDULED"
            if obj.status == "SCHEDULED":
                readonly_fields.extend(["prize", "lottery_name", "draw_time"])
            else:
                readonly_fields.extend(
                    ["prize", "lottery_name", "draw_time", "winning_number"]
                )
        return readonly_fields

    def save_model(self, request, obj: Draw, form, change):
        # ✅ DEFINITIVO: Comparamos con el string "SCHEDULED"
        if "winning_number" in form.changed_data and obj.status == "SCHEDULED":
            winning_number = form.cleaned_data.get("winning_number")
            if winning_number is not None:
                try:
                    message = process_draw_result(
                        draw=obj, winning_number=winning_number
                    )
                    self.message_user(request, message, messages.SUCCESS)
                except DrawProcessingError as e:
                    self.message_user(request, str(e), messages.ERROR)
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error inesperado durante el procesamiento: {e}",
                        messages.ERROR,
                    )
                return

        super().save_model(request, obj, form, change)