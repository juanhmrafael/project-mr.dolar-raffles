# apps/audit/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class GlobalAuditLog(models.Model):
    """
    Modelo proxy no gestionado para la vista de auditoría global en el admin.
    """

    class Meta:
        managed = False
        verbose_name = _("Global Audit Log")
        verbose_name_plural = _("Global Audit Logs")
        app_label = "auditing"
