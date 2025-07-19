# audit/admin/base.py
from django.contrib import admin
from rangefilter.filters import DateRangeFilter


class AuditManagementAdminBase(admin.ModelAdmin):
    """
    Clase base para TODOS los ModelAdmin registrados en el 'audit_site'.
    Centraliza la lógica de permisos para usar nuestro flag 'is_chief_auditor'.
    """

    list_display = ["history_id", "history_date", "history_type"]
    list_filter = [("history_date", DateRangeFilter), "history_type"]
    readonly_fields = ["history_id", "history_date", "history_type", "history_user"]

    # Sobrescribimos CADA uno de los permisos.
    def has_view_permission(self, request, obj=None):
        return request.user.is_chief_auditor

    def has_add_permission(self, request):
        """¿Puede el usuario añadir nuevos objetos?"""
        # Generalmente en auditoría no se añade nada.
        return False

    def has_change_permission(self, request, obj=None):
        """¿Puede el usuario cambiar un objeto existente?"""
        # La auditoría es inmutable.
        return False

    def has_delete_permission(self, request, obj=None):
        """¿Puede el usuario eliminar un objeto?"""
        # La auditoría es inmutable.
        return False

    def has_module_permission(self, request):
        """Controla si el módulo (la app) aparece en el índice."""
        return request.user.is_chief_auditor
