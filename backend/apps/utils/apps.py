# backend/apps/utils/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UtilsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "utils"
    verbose_name = _("Utils")
