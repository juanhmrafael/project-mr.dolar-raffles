# audit/admin.py

from currencies.models import ExchangeRate
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from users.models import CustomGroup

from .admin.base import AuditManagementAdminBase as Base
from .admin.global_audit_log import GlobalAuditLogAdmin
from .admin.group import HistoricalGroupAdmin
from .admin.user import CustomUserAdmin, HistoricalUserAdmin
from .models import GlobalAuditLog

User = get_user_model()
HistoricalUser = User.history.model


class AuditAdminSite(AdminSite):
    """
    Sitio de administración personalizado para auditoría.
    """

    site_header = _("Audit Management")
    site_title = _("Audit Admin")
    index_title = _("Audit Administration")

    def has_permission(self, request):
        """
        Verifica si el usuario tiene permisos para acceder al sitio de administración de auditoría.

        Args:
            request: La solicitud HTTP

        Returns:
            bool: True si el usuario puede acceder, False en caso contrario
        """
        # El usuario debe estar autenticado y activo
        if not request.user.is_authenticated or not request.user.is_active:
            return False

        # Permitir acceso a superusuarios y auditores jefe
        return request.user.is_superuser and request.user.is_chief_auditor


# Crear instancia del sitio de administración de auditoría
audit_admin_site = AuditAdminSite(name="audit_admin")
audit_admin_site.register(User, CustomUserAdmin)
audit_admin_site.register(HistoricalUser, HistoricalUserAdmin)
audit_admin_site.register(CustomGroup.history.model, HistoricalGroupAdmin)

audit_admin_site.register(ExchangeRate.history.model, Base)


audit_admin_site.register(GlobalAuditLog, GlobalAuditLogAdmin, site=audit_admin_site)
