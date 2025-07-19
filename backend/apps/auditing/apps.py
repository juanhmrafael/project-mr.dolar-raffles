from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auditing"
    verbose_name = _("Auditing")