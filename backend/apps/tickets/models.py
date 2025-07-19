# backend/apps/tickets/models.py
"""
Modelos para la gestión de los tickets o números de la rifa.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class Ticket(models.Model):
    """
    Representa un número de ticket único asignado a una participación
    una vez que su pago ha sido aprobado.
    """

    raffle = models.ForeignKey(
        "raffles.Raffle",
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name=_("Raffle"),
    )
    participation = models.ForeignKey(
        "participants.Participation",
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name=_("Participation"),
    )
    ticket_number = models.PositiveIntegerField(_("Ticket Number"))

    assigned_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")
        # Esta restricción de unicidad es CRÍTICA.
        # Asegura que no se pueda asignar el mismo número dos veces en la misma rifa.
        unique_together = ("raffle", "ticket_number")
        ordering = ["raffle", "ticket_number"]
        indexes = [
            # Índice para búsquedas rápidas de un número en una rifa (para determinar ganador).
            models.Index(fields=["raffle", "ticket_number"]),
        ]

    def __str__(self) -> str:
        return f"Ticket #{self.ticket_number} for {self.raffle.title}"
