# backend/apps/payments/payment/admin.py
"""
Configuración del Admin para el modelo Payment.

Este módulo define la interfaz de administración para los pagos, enfocándose en
una presentación clara, acciones de negocio seguras y una orquestación eficiente
de la lógica de negocio delegada a los servicios y formularios.
"""

from typing import Any

from django.contrib import admin, messages
from django.db.models import Case, When
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilter
from simple_history.admin import SimpleHistoryAdmin

from ..models import Payment
from .form import PaymentAdminForm
from .services_sync import approve_payment, revert_approved_payment


class PaymentAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    """
    Interfaz de administración para el modelo Payment.
    """

    # --------------------------------------------------------------------------
    # CONFIGURACIÓN PRINCIPAL
    # --------------------------------------------------------------------------
    form = PaymentAdminForm
    autocomplete_fields = ["participation"]
    actions = [
        "approve_selected_payments",
        "reject_selected_payments",
        "safe_delete_selected",
    ]

    # --------------------------------------------------------------------------
    # CONFIGURACIÓN DE LA VISTA DE LISTA (OPTIMIZADA PARA RENDIMIENTO)
    # --------------------------------------------------------------------------
    list_display = (
        "participant_link",
        "payment_method_used",
        "display_transaction_details",
        "amount_to_pay",
        "currency_paid",
        "payment_date",
        "status",
    )
    list_filter = (
        "status",
        "payment_method_used__method_type",
        ("payment_date", DateRangeFilter),
    )
    search_fields = (
        "participation__full_name",
        "participation__identification_number",
        "transaction_details__reference",
    )
    # Optimización clave: Precarga los datos relacionados en una sola consulta
    # para evitar el problema N+1.
    list_select_related = (
        "participation__raffle",
        "payment_method_used",
        "verified_by",
    )
    ordering = (
        Case(
            When(status="PENDING", then=0),
            When(status="APPROVED", then=1),
            When(status="REJECTED", then=2),
            default=3,
        ),
        "-created_at",
    )

    @admin.display(description=_("Participant"))
    def participant_link(self, obj: Payment) -> str:
        """
        Crea un enlace al formulario de edición del pago usando el nombre del
        participante, lo que es más intuitivo que usar el ID.
        """
        url = reverse("admin:payments_payment_change", args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, obj.participation.full_name)

    @admin.display(description=_("Transaction Details"))
    def display_transaction_details(self, obj: Payment) -> str:
        """
        Muestra los detalles clave de la transacción de forma legible y traducible
        en la vista de lista para una verificación rápida.
        """
        if not obj.transaction_details:
            return "—"

        details = []

        # ✅ Usamos gettext_lazy (_) para las etiquetas estáticas.
        # La función `format_html` se encarga de escapar de forma segura los valores
        # dinámicos (como ref, email, pay_id) para prevenir ataques XSS,
        # mientras que permite que las etiquetas HTML <b> pasen.

        if ref := obj.transaction_details.get("reference"):
            # Translators: "Ref:" is a short label for "Reference Number".
            details.append(format_html("<b>{}:</b> {}", _("Reference"), ref))

        if email := obj.transaction_details.get("email"):
            # Translators: "Email:" is a label for an email address.
            details.append(format_html("<b>{}:</b> {}", _("Email"), email))

        if pay_id := obj.transaction_details.get("binance_pay_id"):
            # Translators: "Pay ID:" is a label for a Binance Pay ID.
            details.append(format_html("<b>{}:</b> {}", _("Pay ID"), pay_id))

        return mark_safe("<br>".join(details))

    # --------------------------------------------------------------------------
    # CONFIGURACIÓN DE LA VISTA DE FORMULARIO (DECLARATIVA Y DINÁMICA)
    # --------------------------------------------------------------------------
    class Media:
        """Añade los assets de JavaScript necesarios para el formulario dinámico."""

        js = ("assets/js/payment_admin_form.js",)

    def get_readonly_fields(
        self, request: HttpRequest, obj: Payment | None = None
    ) -> list[str]:
        """
        Define los campos de solo lectura. Los datos de auditoría y los campos
        calculados son inmutables una vez que el pago es creado.
        """
        if obj:  # Si el objeto ya existe (modo de edición)
            return [
                "participation",
                "payment_method_used",
                "payment_date",
                "amount_to_pay",
                "exchange_rate_applied",
                "payment_hash",
                "ticket_price_at_creation",
                "ticket_count_at_creation",
                "created_at",
                "updated_at",
                "verified_by",
                "verified_at",
                "currency_paid",
            ]
        return []

    def get_fieldsets(
        self, request: HttpRequest, obj: Payment | None = None
    ) -> list[tuple]:
        """
        Construye los fieldsets dinámicamente.

        - En modo de edición, muestra solo los campos 'td_*' relevantes para
          el método de pago del objeto, resolviendo el problema de visualización.
        - En modo de creación, los muestra todos para que JS los controle.
        """
        base_details_fieldset = (
            _("Base Details"),
            {
                "fields": ("participation", "payment_method_used", "payment_date"),
                "description": '<div id="amount-to-pay-display" class="form-row"></div>',
            },
        )
        verification_fieldset = (
            _("Verification Status"),
            {"fields": ("status", "verification_notes")},
        )
        audit_fieldset = (
            _("System & Audit Data (Read-Only)"),
            {
                "fields": (
                    "amount_to_pay",
                    "currency_paid",
                    "exchange_rate_applied",
                    "ticket_price_at_creation",
                    "ticket_count_at_creation",
                    "payment_hash",
                    "verified_by",
                    "verified_at",
                ),
                "classes": ("collapse",),
            },
        )

        # --- LÓGICA DE FIELDSET DINÁMICO ---
        # Por defecto (en creación), mostramos todos los campos virtuales.
        transaction_data_fields = ("td_reference", "td_email", "td_binance_pay_id")

        # Si estamos editando y tenemos un método de pago, filtramos los campos.
        if obj and obj.payment_method_used:
            method_type = obj.payment_method_used.method_type
            FIELD_MAP = {
                "PAGO_MOVIL": ("td_reference",),
                "TRANSFERENCIA": ("td_reference",),
                "ZELLE": ("td_reference", "td_email"),
                "BINANCE": ("td_reference", "td_binance_pay_id"),
            }

            # Obtenemos la tupla de campos correcta del mapa.
            transaction_data_fields = FIELD_MAP.get(method_type, ())

        transaction_data_fieldset = (
            _("Transaction Data"),
            {
                "fields": transaction_data_fields,
                "classes": ("dynamic-fields",),  # La clase ayuda a JS en modo creación.
            },
        )

        # --- Composición final del layout ---
        layout = [
            base_details_fieldset,
            transaction_data_fieldset,
            verification_fieldset,
        ]
        if obj:
            layout.append(audit_fieldset)
        return layout

    # --------------------------------------------------------------------------
    # MÉTODOS DE ORQUESTACIÓN Y ACCIONES (LÓGICA DE NEGOCIO)
    # --------------------------------------------------------------------------

    def save_model(
        self, request: HttpRequest, obj: Payment, form: Any, change: bool
    ) -> None:
        """
        Orquesta las acciones de negocio basadas en la transición de estado al guardar.
        """
        original_status = form.initial.get("status")
        new_status = form.cleaned_data.get("status")

        super().save_model(request, obj, form, change)

        if original_status == new_status and change:
            return  # Sin cambio de estado en un objeto existente, no hay acción de negocio.

        try:
            if new_status == "APPROVED":
                approve_payment(payment=obj, verified_by=request.user)
                messages.success(
                    request, _("Payment approved and tickets assigned successfully.")
                )
            elif original_status == "APPROVED" and new_status in [
                "PENDING",
                "REJECTED",
            ]:
                revert_approved_payment(payment=obj, reverted_by=request.user)
                obj.verified_by = request.user
                obj.verified_at = timezone.now()
                obj.save(update_fields=["verified_by", "verified_at"])
                messages.warning(
                    request,
                    _(
                        "Payment status changed and associated tickets have been revoked."
                    ),
                )
            elif change:  # Cualquier otro cambio de estado en un objeto existente
                obj.verified_by = request.user
                obj.verified_at = timezone.now()
                obj.save(update_fields=["verified_by", "verified_at"])
        except Exception as e:
            messages.error(
                request,
                _("An error occurred while processing the state change: ") + str(e),
            )

    def delete_model(self, request: HttpRequest, obj: Payment) -> None:
        """
        Sobrescribe la eliminación para revocar tickets de pagos aprobados.
        """
        if obj.status == "APPROVED":
            try:
                revert_approved_payment(payment=obj, reverted_by=request.user)
                messages.warning(request, _("Associated tickets have been revoked."))
            except Exception as e:
                messages.error(
                    request,
                    _("Could not revoke tickets. Deletion cancelled. Error: %(error)s")
                    % {"error": e},
                )
                return
        super().delete_model(request, obj)

    def get_actions(self, request: HttpRequest) -> dict:
        """Reemplaza la acción de borrado por defecto por una segura."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    @admin.action(description=_("Approve selected payments"))
    def approve_selected_payments(
        self, request: HttpRequest, queryset: QuerySet
    ) -> None:
        """Acción en lote para aprobar pagos."""
        self._bulk_process_payments(request, queryset, self._approve_action)

    @admin.action(description=_("Reject selected payments"))
    def reject_selected_payments(
        self, request: HttpRequest, queryset: QuerySet
    ) -> None:
        """Acción en lote para rechazar pagos, revocando tickets si es necesario."""
        self._bulk_process_payments(request, queryset, self._reject_action)

    @admin.action(description=_("Delete selected payments (safe)"))
    def safe_delete_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Acción en lote para eliminar pagos, revocando tickets si es necesario."""
        self._bulk_process_payments(request, queryset, self._delete_action)

    # --------------------------------------------------------------------------
    # MÉTODOS AUXILIARES PRIVADOS (REUTILIZACIÓN Y LIMPIEZA)
    # --------------------------------------------------------------------------

    def _bulk_process_payments(
        self, request: HttpRequest, queryset: QuerySet, action_func: callable
    ) -> None:
        """
        Motor reutilizable para procesar acciones en lote de forma segura.
        """
        success_count = 0
        error_count = 0
        for payment in queryset:
            try:
                action_func(payment, request.user)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    _("Error processing payment %(id)s: %(error)s")
                    % {"id": payment.id, "error": e},
                    messages.ERROR,
                )

        action_name = action_func.__name__.replace("_action", "").capitalize()
        if success_count:
            messages.success(
                request,
                _(f"{success_count} payments were successfully {action_name}d."),
            )
        if error_count:
            messages.warning(request, _(f"Failed to process {error_count} payments."))

    def _approve_action(self, payment: Payment, user: Any) -> None:
        """Lógica de negocio para la acción de aprobar."""
        if payment.status != "APPROVED":
            approve_payment(payment=payment, verified_by=user)

    def _reject_action(self, payment: Payment, user: Any) -> None:
        """Lógica de negocio para la acción de rechazar."""
        if payment.status != "REJECTED":
            if payment.status == "APPROVED":
                revert_approved_payment(payment=payment, reverted_by=user)
            payment.status = "REJECTED"
            payment.verified_by = user
            payment.verified_at = timezone.now()
            payment.save(update_fields=["status", "verified_by", "verified_at"])

    def _delete_action(self, payment: Payment, user: Any) -> None:
        """Lógica de negocio para la acción de eliminar."""
        if payment.status == "APPROVED":
            revert_approved_payment(payment=payment, reverted_by=user)
        payment.delete()

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict | None = None,
    ) -> Any:
        """
        Inyecta datos para JavaScript en la vista de edición.
        Este método ya no es estrictamente necesario para la visibilidad, pero
        se mantiene por si se necesita para otra lógica de JS en el futuro.
        """
        extra_context = extra_context or {}
        payment = self.get_object(request, object_id)
        if payment and payment.payment_method_used:
            js_data = f"""<script>window.paymentAdminData = {{ methodType: "{payment.payment_method_used.method_type}" }};</script>"""
            extra_context["js_data"] = mark_safe(js_data)
        return super().change_view(request, object_id, form_url, extra_context)
