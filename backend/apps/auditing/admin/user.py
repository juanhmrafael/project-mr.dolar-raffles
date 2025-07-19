# auditing/admin/user.py
import hashlib

from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin
from apps.utils.validators import validate_natural_person_id

from .base import AuditManagementAdminBase as Base

User = get_user_model()
HistoricalUser = User.history.model


class CustomUserAdmin(SimpleHistoryAdmin, UserAdmin):
    """
    Admin para el modelo User personalizado.

    Integra simple-history para una auditoría completa de cambios y proporciona
    funcionalidades personalizadas como la vista previa de avatares y la búsqueda
    por número de identificación hasheado.

    IMPORTANTE: Hereda de UserAdmin para manejar correctamente el hash de contraseñas.
    """

    # --- Configuración de la lista de visualización ---
    list_display = (
        "email",
        "first_name",
        "last_name",
        "avatar_preview",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    # --- Configuración del formulario de edición ---
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "identification_number", "avatar")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_chief_auditor",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # --- Configuración del formulario de creación ---
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "identification_number",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined")

    def avatar_preview(self, obj: get_user_model) -> SafeString:
        """
        Genera una miniatura HTML del avatar del usuario.
        """
        if obj.avatar:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url,
            )
        return _("No avatar")

    avatar_preview.short_description = _("Avatar Preview")

    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet, search_term: str
    ) -> tuple[QuerySet, bool]:
        """
        Sobrescribe la búsqueda para incluir la búsqueda por hash del número de identificación.
        """
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        try:
            validate_natural_person_id(search_term)
            search_hash = hashlib.sha256(
                search_term.strip().upper().encode("utf-8")
            ).hexdigest()
            queryset |= self.model.objects.filter(
                identification_number_hash=search_hash
            )
        except ValidationError:
            pass

        return queryset, use_distinct


class HistoricalUserAdmin(Base):
    """
    Admin para el historial de usuarios.
    """

    list_display = Base.list_display + ["email"]
    search_fields = ("email", "first_name", "last_name")

    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet, search_term: str
    ) -> tuple[QuerySet, bool]:
        """
        Sobrescribe la búsqueda para incluir la búsqueda por hash del número de identificación.
        """
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        try:
            validate_natural_person_id(search_term)
            search_hash = hashlib.sha256(
                search_term.strip().upper().encode("utf-8")
            ).hexdigest()
            queryset |= self.model.objects.filter(
                identification_number_hash=search_hash
            )
        except ValidationError:
            pass

        return queryset, use_distinct
