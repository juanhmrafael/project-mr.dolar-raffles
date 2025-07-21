# backend/apps/raffles/prize/admin.py (VERSIÓN CON ACCIÓN DE REVOCAR)
from datetime import timedelta

from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from ..models import Draw, Prize
from ..service_sync import (
    DrawProcessingError,
    RevokePrizeError,
    process_draw_result,
    revoke_prize_assignment,
)


class PrizeInline(admin.StackedInline):
    model = Prize
    extra = 0
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("display_order", "level_title"),
                    "name",
                    "description",
                    "image",
                )
            },
        ),
    )
    classes = ["collapse"]


# --- Formulario y FormSet para controlar la lógica del inline ---


class DrawInlineForm(forms.ModelForm):
    class Meta:
        model = Draw
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lógica para hacer el campo de número ganador de solo lectura si el sorteo no está programado
        instance = kwargs.get("instance")
        if instance and instance.pk and instance.status != "SCHEDULED":
            self.fields["winning_number"].widget.attrs["disabled"] = True


# --- El Inline Inteligente ---


class DrawInline(admin.TabularInline):
    model = Draw
    form = DrawInlineForm  # Usamos nuestro formulario personalizado
    extra = 1

    # Campos a mostrar en el inline
    fields = ("lottery_name", "draw_time", "status", "winning_number")
    # Hacemos de solo lectura los campos que no deben cambiarse aquí.
    # 'winning_number' se controla dinámicamente con el formulario.
    readonly_fields = ("status",)


class PrizeAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    list_display = (
        "name",
        "raffle",
        "level_title",
        "is_delivered_status",
        "winner_display",
    )
    list_filter = ("raffle__title", "delivered_at")
    search_fields = (
        "name",
        "level_title",
        "raffle__title",
        "winner_participation__full_name",
    )

    inlines = [DrawInline]
    autocomplete_fields = ["raffle"]

    # ✅ AHORA TENEMOS DOS ACCIONES: la normal y la de emergencia.
    actions = ["revoke_and_rerun_draw", "force_reset_winner"]

    # --- LÓGICA DE VISUALIZACIÓN (sin cambios) ---
    def get_readonly_fields(self, request, obj=None):
        base_readonly = [
            "winner_participation",
            "winner_ticket_number",
            "image_preview",
            "delivered_image_preview",
        ]
        if obj and obj.winner_participation and obj.delivered_at:
            base_readonly.extend(["delivered_at", "delivered_image"])
        elif not obj or not obj.winner_participation:
            base_readonly.extend(["delivered_at", "delivered_image"])
        return base_readonly

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = (
            (
                None,
                {
                    "fields": (
                        "raffle",
                        "display_order",
                        "level_title",
                        "name",
                        "description",
                    )
                },
            ),
            (_("Promotional Image"), {"fields": ("image", "image_preview")}),
        )
        if obj and obj.winner_participation:
            winner_fieldset = (
                _("Winner & Delivery Details"),
                {
                    "description": _(
                        "Un ganador ha sido asignado. Para registrar la entrega, complete la fecha y suba la foto del ganador."
                    ),
                    "fields": (
                        "winner_participation",
                        "winner_ticket_number",
                        "delivered_at",
                        "delivered_image",
                        "delivered_image_preview",
                    ),
                },
            )
            return base_fieldsets + (winner_fieldset,)
        return base_fieldsets

    def save_model(self, request, obj: Prize, form, change):
        if "delivered_image" in form.changed_data and not obj.delivered_at:
            obj.delivered_at = timezone.now()
            self.message_user(
                request,
                _(
                    "La fecha de entrega se ha establecido automáticamente porque se subió una foto del ganador."
                ),
                messages.INFO,
            )
        super().save_model(request, obj, form, change)

    # ✅ NUEVO: La lógica de negocio para la acción de revocación.
    @admin.action(description=_("Revocar premio y programar nuevo sorteo"))
    def revoke_and_rerun_draw(self, request, queryset):
        """
        Invoca el servicio central para revocar premios seleccionados.
        """
        revoked_count = 0
        for prize in queryset:
            try:
                revoke_prize_assignment(prize)
                revoked_count += 1
            except RevokePrizeError as e:
                self.message_user(request, str(e), messages.ERROR)

        if revoked_count > 0:
            self.message_user(
                request,
                _(
                    f"{revoked_count} premio(s) han sido revocados y se han programado nuevos sorteos."
                ),
                messages.SUCCESS,
            )

    @admin.action(
        description=_("Forzar reseteo de ganador (corrige sorteos eliminados)")
    )
    @transaction.atomic
    def force_reset_winner(self, request, queryset):
        """
        Resetea un premio con un ganador "huérfano" cuyo sorteo fue eliminado.
        """
        fixed_count = 0
        for prize in queryset:
            # --- Validaciones de seguridad ---
            if not prize.winner_participation:
                self.message_user(
                    request,
                    _(
                        f"El premio '{prize.name}' no tiene ganador. No se necesita esta acción."
                    ),
                    messages.WARNING,
                )
                continue
            if prize.is_delivered:
                self.message_user(
                    request,
                    _(
                        f"El premio '{prize.name}' ya fue entregado y no puede ser reseteado."
                    ),
                    messages.ERROR,
                )
                continue
            # La condición clave: solo actuamos si NO hay un sorteo completado.
            if Draw.objects.filter(prize=prize, status="COMPLETED").exists():
                self.message_user(
                    request,
                    _(
                        f"El premio '{prize.name}' tiene un sorteo válido. Use la acción de revocación estándar."
                    ),
                    messages.ERROR,
                )
                continue

            # --- Lógica de Corrección ---
            prize.winner_participation = None
            prize.winner_ticket_number = None
            prize.save()

            # Creamos un nuevo sorteo para poder volver a sortearlo.
            # Usamos el nombre de lotería por defecto del modelo Draw.
            Draw.objects.create(
                prize=prize,
                lottery_name=Draw._meta.get_field("lottery_name").get_default(),
                draw_time=timezone.now() + timedelta(days=1),
                status="SCHEDULED",
            )
            fixed_count += 1

        if fixed_count > 0:
            self.message_user(
                request,
                _(
                    f"{fixed_count} premio(s) con ganadores huérfanos han sido reseteados y reprogramados."
                ),
                messages.SUCCESS,
            )

    # --- Funciones de visualización (sin cambios) ---
    @admin.display(description=_("Image Preview"))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.image.url,
            )
        return _("No image")

    @admin.display(description=_("Winner Photo Preview"))
    def delivered_image_preview(self, obj):
        if obj.delivered_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.delivered_image.url,
            )
        return _("No image")

    @admin.display(description=_("Winner"), ordering="winner_participation__full_name")
    def winner_display(self, obj: Prize):
        if obj.winner_participation:
            return f"{obj.winner_participation.full_name} (Ticket #{obj.winner_ticket_number})"
        return "N/A"

    @admin.display(boolean=True, description=_("Delivered?"), ordering="delivered_at")
    def is_delivered_status(self, obj: Prize):
        return obj.is_delivered

    # ✅ LA LÓGICA MÁS IMPORTANTE Y COMPLETA ESTÁ AQUÍ
    @transaction.atomic  # Envolvemos toda la operación en una transacción
    def save_formset(self, request, form, formset, change):
        """
        Maneja la creación, actualización Y ELIMINACIÓN de sorteos (inlines),
        actualizando el premio padre de forma consistente.
        """
        # --- PASO 1: MANEJAR LAS ELIMINACIONES ---
        # Iteramos sobre los formularios marcados para borrado ANTES de que se borren.
        for deleted_form in formset.deleted_forms:
            # `instance` es el objeto Draw que está a punto de ser eliminado
            draw_to_delete = deleted_form.instance
            prize = form.instance  # El premio padre

            # Condición de causalidad: ¿Este Draw fue el que asignó el ganador actual?
            if (
                draw_to_delete.pk  # Debe ser un objeto existente
                and draw_to_delete.status == "COMPLETED"
                and prize.winner_participation  # El premio debe tener un ganador
                and prize.winner_ticket_number == draw_to_delete.winning_number
            ):
                # ¡Sí lo fue! Reseteamos el premio.
                prize.winner_participation = None
                prize.winner_ticket_number = None
                prize.save()  # Guardamos el cambio en el premio

                self.message_user(
                    request,
                    _(
                        "El ganador fue reseteado porque el sorteo que lo generó fue eliminado."
                    ),
                    messages.WARNING,
                )

        # --- PASO 2: DEJAR QUE DJANGO HAGA SU GUARDADO ESTÁNDAR ---
        # Esto guardará los cambios en los formularios y eliminará los marcados.
        super().save_formset(request, form, formset, change)

        # --- PASO 3: MANEJAR CREACIONES/ACTUALIZACIONES (Asignar un nuevo ganador) ---
        # Iteramos sobre los formularios que NO fueron borrados.
        for inline_form in formset.forms:
            if inline_form in formset.deleted_forms:
                continue  # Saltamos los que ya manejamos

            if not inline_form.is_valid() or not inline_form.has_changed():
                continue

            # El disparador: ¿se introdujo un número ganador?
            if "winning_number" in inline_form.changed_data:
                draw_instance = inline_form.instance
                winning_number = inline_form.cleaned_data.get("winning_number")

                if draw_instance.status == "SCHEDULED" and winning_number is not None:
                    try:
                        message = process_draw_result(
                            draw=draw_instance, winning_number=winning_number
                        )
                        self.message_user(request, message, messages.SUCCESS)
                    except DrawProcessingError as e:
                        self.message_user(request, str(e), messages.ERROR)
