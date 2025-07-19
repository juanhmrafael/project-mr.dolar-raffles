# backend/apps/currencies/models.py
"""
Modelos para la gestión de monedas y tasas de cambio.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class ExchangeRate(models.Model):
    """
    Almacena el historial diario de la tasa de cambio USD a VEF.
    """

    SOURCE_CHOICES = [
        ("BCV_SCRAPER", _("BCV Scraper")),
        ("MANUAL_INPUT", _("Manual Input")),
    ]

    date = models.DateField(_("Date"), unique=True, db_index=True)
    rate = models.DecimalField(_("Rate (VEF per USD)"), max_digits=10, decimal_places=4)
    source = models.CharField(_("Source"), max_length=20, choices=SOURCE_CHOICES)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Exchange Rate")
        verbose_name_plural = _("Exchange Rates")
        ordering = ["-date"]
        get_latest_by = "date"

    def __str__(self) -> str:
        return f"{self.date}: {self.rate} VEF/USD ({self.get_source_display()})"
