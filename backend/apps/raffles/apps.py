from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class RafflesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'raffles'
    verbose_name = _("Raffles Management")