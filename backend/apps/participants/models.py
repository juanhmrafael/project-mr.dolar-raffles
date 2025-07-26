# backend/apps/participants/models.py
"""
Modelos de datos para los participantes de las rifas.
"""

import hashlib

from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from utils.validators import (
    validate_full_name,
    validate_natural_person_id,
)


class Participation(models.Model):
    """
    Representa la participación de una persona en una rifa específica.

    Almacena los datos de contacto del participante y la cantidad de tickets
    que desea comprar. Los datos personales sensibles se hashean para
    permitir búsquedas seguras sin exponer la información en texto plano.
    """

    raffle = models.ForeignKey(
        "raffles.Raffle",
        on_delete=models.CASCADE,
        related_name="participations",
        verbose_name=_("Raffle"),
    )

    # --- Datos de contacto del participante ---
    full_name = models.CharField(
        _("Full Name"),
        max_length=255,
        validators=[validate_full_name],
    )
    phone = models.CharField(
        _("Phone Number"),
        max_length=20,
        help_text=_(
            "Enter the 11-digit cell phone number."
        ),
    )
    email = models.EmailField(_("Email Address"))
    identification_number = models.CharField(
        _("Identification Number"),
        max_length=20,
        validators=[validate_natural_person_id],
        help_text=format_html(
            "{}<br><b>V</b>: Venezolano | <b>E</b>: Extranjero | <b>P</b>: Pasaporte",
            _(
                "Format: L-NNNNNNNN (e.g., V-12345678). It will be formatted automatically."
            ),
        ),
    )

    # --- Campos de hash para búsquedas seguras y optimizadas ---
    phone_hash = models.CharField(max_length=64, editable=False)
    email_hash = models.CharField(max_length=64, editable=False)
    identification_number_hash = models.CharField(max_length=64, editable=False)

    ticket_count = models.PositiveIntegerField(_("Ticket Count"), default=1)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last Updated At"), auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Participation")
        verbose_name_plural = _("Participations")
        ordering = ["-created_at"]
        # Índice compuesto para la consulta de tickets por 3 factores.
        # CRÍTICO para el rendimiento de la consulta del participante.
        indexes = [
            models.Index(
                fields=[
                    "raffle",
                    "identification_number_hash",
                    "phone_hash",
                    "email_hash",
                ],
                name="ticket_lookup_idx",
            )
        ]

    def __str__(self) -> str:
        formatted_date = self.created_at.strftime("%d/%m/%Y")
        return f" {self.raffle.title} | {formatted_date} - ({self.ticket_count}) {self.full_name}"

    def _hash_field(self, field_data: str) -> str:
        """Función de utilidad interna para hashear un campo usando SHA-256."""
        return hashlib.sha256(field_data.strip().lower().encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para calcular y almacenar los hashes
        de los campos de identificación antes de guardar el objeto.
        """
        self.phone_hash = self._hash_field(self.phone)
        self.email_hash = self._hash_field(self.email)
        self.identification_number_hash = self._hash_field(self.identification_number)

        # Nota: Los campos PII (phone, email, identification_number) deberían
        # ser encriptados. Por simplicidad en este paso, los dejamos en texto plano,
        # pero en el siguiente paso integraremos la encriptación.

        super().save(*args, **kwargs)
