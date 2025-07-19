from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from ..draw.admin import DrawInline
from ..models import Prize


class PrizeInline(admin.StackedInline):
    """
    Permite ver y añadir Premios (Prizes) directamente desde la vista
    de una Rifa (Raffle).
    """

    model = Prize
    extra = 0
    # Usamos fieldsets para organizar mejor los campos del inline.
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


class PrizeAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    """
    Admin para el modelo Prize.
    """

    list_display = (
        "name",
        "raffle",
        "level_title",
        "display_order",
        "winner_ticket_number",
    )
    list_filter = ("raffle__title",)
    search_fields = ("name", "level_title", "raffle__title")

    # Campos que no deben ser editados directamente por el admin.
    readonly_fields = (
        "winner_participation",
        "winner_ticket_number",
        "delivered_at",
        "image_preview",
        "delivered_image_preview",
    )

    # Muestra los sorteos asociados directamente en la página del premio.
    inlines = [DrawInline]

    fieldsets = (
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
        (
            _("Winner Details"),
            {
                "classes": ("collapse",),
                "fields": (
                    "winner_participation",
                    "winner_ticket_number",
                    "delivered_at",
                    "delivered_image",
                    "delivered_image_preview",
                ),
            },
        ),
    )
    autocomplete_fields = ["raffle"]

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
