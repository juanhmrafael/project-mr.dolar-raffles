from django.contrib import admin
from django.db.models import Count, Q, Sum
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from payments.models import Payment
from simple_history.admin import SimpleHistoryAdmin

from ..models import Raffle
from ..prize.admin import PrizeInline


class RaffleAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    list_display = ("title", "status", "is_active", "ticket_price", "end_date")
    list_filter = ("status", "is_active", "currency")
    search_fields = ("title", "slug")
    ordering = ("-start_date",)

    # --- Widget mejorado para la selección de muchos-a-muchos ---
    filter_horizontal = ("available_payment_methods",)

    prepopulated_fields = {"slug": ("title",)}
    inlines = [PrizeInline]

    def get_fieldsets(self, request, obj=None):
        """
        Define la estructura del formulario, organizando los campos en secciones lógicas.
        El reporte de resumen solo se muestra para rifas ya existentes.
        """
        base_fieldsets = [
            (
                _("Step 1: Identity & Visibility"),
                {
                    "description": _(
                        "Set the main details of the raffle and control if it's visible to the public."
                    ),
                    "fields": (
                        ("title", "slug"),
                        "image",
                        "promotional_message",
                        ("status", "is_active"),
                    ),
                },
            ),
            (
                _("Step 2: Rules & Pricing"),
                {
                    "fields": (
                        ("currency", "ticket_price"),
                        ("total_tickets", "min_ticket_purchase"),
                    )
                },
            ),
            (
                _("Step 3: Available Payment Methods"),
                {
                    "description": _(
                        "Select which payment accounts participants can use for this specific raffle."
                    ),
                    "fields": ("available_payment_methods",),
                },
            ),
            (_("Step 4: Timeline"), {"fields": (("start_date", "end_date"),)}),
            (
                _("Step 5: Full Description"),
                {"classes": ("collapse",), "fields": ("description",)},
            ),
        ]

        # Añadimos el fieldset del reporte solo si estamos editando un objeto existente.
        if obj:
            base_fieldsets.append(
                (_("Raffle Summary"), {"fields": ("get_report_summary",)})
            )

        return base_fieldsets

    def get_search_results(self, request, queryset, search_term):
        """
        Sobrescribe la búsqueda para el autocompletado.

        Si la petición viene de un widget de autocompletado, se filtra para
        mostrar únicamente las rifas que están activamente 'En Progreso'.
        Esto previene que se creen participaciones para rifas finalizadas,
        canceladas o en procesamiento.
        """
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # ✅ CORRECCIÓN: Filtramos por el estado de la rifa.
        # Si la petición viene de un autocompletado, aplicamos el filtro estricto.
        if "/autocomplete/" in request.path:
            queryset = queryset.filter(status=Raffle.Status.IN_PROGRESS)

        return queryset, use_distinct

    @admin.display(description=_("Live Report Summary"))
    def get_report_summary(self, obj: Raffle) -> str:
        """
        Calcula y muestra un resumen en tiempo real del estado de la rifa.
        Utiliza una construcción de cadenas segura para evitar errores de formato.
        """
        if not obj.pk:
            return _("Save the raffle to see the summary.")

        report = Payment.objects.filter(participation__raffle_id=obj.pk).aggregate(
            approved_participations=Count("participation", filter=Q(status="APPROVED")),
            pending_participations=Count("participation", filter=Q(status="PENDING")),
            tickets_sold=Sum(
                "participation__ticket_count", filter=Q(status="APPROVED")
            ),
        )

        tickets_sold = report.get("tickets_sold") or 0
        pending_participations = report.get("pending_participations") or 0
        tickets_available = obj.total_tickets - tickets_sold

        # ✅ CORRECCIÓN: Construimos el HTML por partes para evitar errores de f-string.
        # Este enfoque es inmune a problemas de indentación.

        style_html = """
        <style>
            .report-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
            .report-item { border: 1px solid #eee; padding: 10px; border-radius: 4px; }
            .report-item h4 { margin-top: 0; }
        </style>
        """

        tickets_html = format_html(
            """
            <div class="report-item">
                <h4>{}</h4>
                <p><b>{}:</b> {}</p>
                <p><b>{}:</b> {}</p>
                <p><b>{}:</b> {}</p>
            </div>
            """,
            _("Tickets Status"),
            _("Sold"),
            tickets_sold,
            _("Available"),
            tickets_available,
            _("Total"),
            obj.total_tickets,
        )

        queue_html = format_html(
            """
            <div class="report-item">
                <h4>{}</h4>
                <p><b>{}:</b> {}</p>
            </div>
            """,
            _("Verification Queue"),
            _("Pending Payments"),
            pending_participations,
        )

        # Concatenamos todas las partes para formar el HTML final.
        final_html = f"""
        {style_html}
        <div class="report-grid">
            {tickets_html}
            {queue_html}
        </div>
        """

        return mark_safe(final_html)

    def get_readonly_fields(self, request, obj=None):
        """
        Define los campos que serán de solo lectura.
        - `get_report_summary` siempre es de solo lectura.
        - Las reglas de la rifa se bloquean si la rifa ya no está en progreso.
        """
        # El campo de reporte es un método, siempre es de solo lectura.
        readonly_fields = ["get_report_summary"]

        # if obj:
        #     readonly_fields.extend(
        #         [
        #             "currency",
        #             "ticket_price",
        #             "total_tickets",
        #             "min_ticket_purchase",
        #             "start_date",
        #         ]
        #     )

        return readonly_fields
