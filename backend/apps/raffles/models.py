# backend/raffles/models.py
"""
Modelos de datos para la gestión de Rifas y Premios.

Estos modelos forman el núcleo del sistema de rifas, definiendo la estructura
de los sorteos y los premios asociados a cada uno.
"""

from datetime import datetime

# En el futuro, importaremos el mixin de optimización de imágenes.
# from core.mixins import ImageOptimizationMixin
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from utils.enums import CurrencyChoices

# Importamos las funciones para generar las rutas de las imágenes.
from utils.storage import prize_image_path, raffle_banner_path, winner_image_path


class Raffle(models.Model):  # Futuro: heredar de ImageOptimizationMixin
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", _("In Progress")
        PROCESSING_WINNERS = "PROCESSING_WINNERS", _("Processing Winners")
        FINISHED = "FINISHED", _("Finished")
        CANCELLED = "CANCELLED", _("Cancelled")

    """
    Representa una rifa o sorteo.

    Contiene toda la información general, como el precio del ticket, la cantidad
    total de tickets, y el estado de actividad.
    """

    title = models.CharField(_("Title"), max_length=200)
    slug = models.SlugField(
        _("Slug"),
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("Unique identifier for URL. Auto-generated from title."),
    )
    description = models.TextField(_("Description"), blank=True)
    promotional_message = models.TextField(
        _("Promotional Message"),
        blank=True,  # Permite que el campo esté vacío a nivel de BD
        help_text=_("Catchy text to display when this is the main raffle."),
    )
    currency = models.CharField(
        _("Currency"),
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.USD,
    )
    ticket_price = models.DecimalField(
        _("Ticket Price"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Price in the selected currency."),
    )
    total_tickets = models.PositiveIntegerField(_("Total Tickets"))
    min_ticket_purchase = models.PositiveIntegerField(
        _("Minimum Ticket Purchase"),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Minimum number of tickets a participant must buy at once."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        blank=False,
        null=False,
        db_index=True,
    )
    is_active = models.BooleanField(
        _("Is Publicly Visible?"),
        default=True,
        help_text=_(
            "Check this to make the raffle visible to participants on the website."
        ),
    )
    image = models.ImageField(
        _("Main Image"),
        upload_to=raffle_banner_path,
        help_text=_("Banner image for the raffle."),
    )
    available_payment_methods = models.ManyToManyField(
        "payments.PaymentMethod",
        verbose_name=_("Available Payment Methods"),
        help_text=_("Select the payment methods available for this raffle."),
    )
    start_date = models.DateTimeField(_("Start Date"), default=datetime.now)
    end_date = models.DateTimeField(
        _("End Date"),
        null=True,
        blank=True,
        help_text=_(
            "Optional. Leave blank if the raffle ends based on manual decision or ticket sales."
        ),
    )

    # --- Campo para el historial de cambios ---
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Raffle")
        verbose_name_plural = _("Raffles")
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "end_date"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def ticket_number_digits(self) -> int:
        """
        Calcula el número de dígitos necesarios para mostrar los números de ticket.

        Basado en el total de tickets, determina la longitud del número más alto
        (ej., si total_tickets es 10000, los tickets van de 0 a 9999. El número
        más alto es 9999, que tiene 4 dígitos).

        Returns:
            int: El número de dígitos para el padding.
        """
        if not self.total_tickets or self.total_tickets < 1:
            return 0  # Caso borde: si no hay tickets, no hay dígitos.

        # La lógica es la longitud del número de ticket más alto (total_tickets - 1).
        # Por ejemplo, para 100 tickets (0-99), la longitud es len(str(99)) = 2.
        # Para 10000 tickets (0-9999), la longitud es len(str(9999)) = 4.
        return len(str(self.total_tickets - 1))
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar un slug único si no existe.
        """
        if not self.slug:
            base_slug = slugify(self.title)
            # Añadimos un timestamp para garantizar unicidad absoluta y evitar colisiones.
            timestamp = datetime.now().strftime("%y%m%d%H%M%S")
            self.slug = f"{base_slug}-{timestamp}"

        # En el futuro, aquí se llamará a self.optimize_images()
        super().save(*args, **kwargs)


class Prize(models.Model):  # Futuro: heredar de ImageOptimizationMixin
    """
    Representa un premio específico asociado a una rifa.

    Permite definir premios para posiciones individuales o rangos de posiciones.
    """

    raffle = models.ForeignKey(
        Raffle,
        on_delete=models.CASCADE,
        related_name="prizes",
        verbose_name=_("Raffle"),
    )

    # --- Campos de Orden y Título Flexibles (NUEVO) ---
    display_order = models.PositiveIntegerField(
        _("Display Order"),
        default=1,
        help_text=_("Order of importance for display (1 = most important)."),
    )
    level_title = models.CharField(
        _("Prize Level Title"),
        max_length=100,
        blank=True,
        help_text=_("E.g., 'Grand Prize', 'Second Prize', 'Consolation Prize'."),
    )

    name = models.CharField(_("Prize Name"), max_length=100)
    description = models.TextField(_("Prize Description"), blank=True)

    # --- Campos de imágenes ---
    image = models.ImageField(
        _("Prize Image"),
        upload_to=prize_image_path,
        null=True,
        blank=True,
        help_text=_("Promotional image of the prize."),
    )
    delivered_image = models.ImageField(
        _("Winner Photo"),
        upload_to=winner_image_path,
        null=True,
        blank=True,
        help_text=_("Photo of the winner with their prize."),
    )

    # --- Campos para registrar al ganador ---
    winner_participation = models.ForeignKey(
        "participants.Participation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_prizes",
        verbose_name=_("Winner"),
    )
    winner_ticket_number = models.PositiveIntegerField(
        _("Winner Ticket Number"), null=True, blank=True
    )
    delivered_at = models.DateTimeField(_("Delivered At"), null=True, blank=True)

    # --- Historial de cambios ---
    history = HistoricalRecords()

    # --- Atributo para el futuro mixin de optimización ---
    # image_fields_to_optimize = ['image', 'delivered_image']

    class Meta:
        verbose_name = _("Prize")
        verbose_name_plural = _("Prizes")
        ordering = ["raffle", "display_order"]
        indexes = [
            models.Index(fields=["raffle", "display_order"]),
        ]

    def __str__(self) -> str:
        display_name = self.level_title or self.name
        return f"{display_name} ({self.raffle.title})"

    def save(self, *args, **kwargs):
        # En el futuro, aquí se llamará a self.optimize_images()
        super().save(*args, **kwargs)

    @property
    def is_delivered(self) -> bool:
        """Propiedad para verificar fácilmente si el premio ya fue entregado."""
        return self.delivered_at is not None


class Draw(models.Model):
    """
    Representa un evento de sorteo externo al que está vinculado un premio.
    Este modelo desacopla la lógica del sorteo de la definición del premio.
    """

    STATUS_CHOICES = [
        ("SCHEDULED", _("Scheduled")),
        ("COMPLETED", _("Completed")),
        ("ROLLED_OVER", _("Rolled Over")),
    ]

    prize = models.ForeignKey(
        Prize, on_delete=models.CASCADE, related_name="draws", verbose_name=_("Prize")
    )
    lottery_name = models.CharField(
        _("Lottery Name"), max_length=100, default="Lotería del Táchira"
    )
    draw_time = models.DateTimeField(
        _("Draw Time"), help_text=_("Date and time of the external lottery draw.")
    )

    winning_number = models.PositiveIntegerField(
        _("Winning Number"), null=True, blank=True
    )
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default="SCHEDULED"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Draw")
        verbose_name_plural = _("Draws")
        ordering = ["-draw_time"]
        indexes = [
            models.Index(fields=["prize", "draw_time"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return (
            f"Draw for {self.prize.name} at {self.draw_time.strftime('%Y-%m-%d %H:%M')}"
        )
