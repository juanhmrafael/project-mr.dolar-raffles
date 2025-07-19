# auditing/admin_registration.py

def register_audit_admins():
    """
    Función para registrar todos los ModelAdmin en el audit_admin_site.
    Se llama desde AppConfig.ready() para evitar dependencias circulares.
    """
    from django.contrib.auth import get_user_model

    from .admin.global_audit_log import GlobalAuditLogAdmin
    from .admin.user import CustomUserAdmin, HistoricalUserAdmin
    from .models import GlobalAuditLog
    
    # Importaciones locales para romper el ciclo
    from .sites import audit_admin_site

    User = get_user_model()
    HistoricalUser = User.history.model

    # Registro manual
    audit_admin_site.register(User, CustomUserAdmin)
    audit_admin_site.register(HistoricalUser, HistoricalUserAdmin)
    audit_admin_site.register(GlobalAuditLog, GlobalAuditLogAdmin)