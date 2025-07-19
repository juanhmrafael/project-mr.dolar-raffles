# backend/apps/utils/enums.py
"""
Módulo para centralizar enumeraciones y choices reutilizables en todo el proyecto.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class CurrencyChoices(models.TextChoices):
    """
    Define las monedas soportadas en el sistema.
    Usar TextChoices es la práctica moderna y recomendada.
    """

    USD = "USD", _("US Dollar")
    VEF = "VEF", _("Venezuelan Bolívar")
