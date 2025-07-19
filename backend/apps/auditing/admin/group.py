from .base import AuditManagementAdminBase as Base


class HistoricalGroupAdmin(Base):
    """
    Admin para el historial de grupos.
    """
    list_display = Base.list_display + ["name"]
    search_fields = ("name",)