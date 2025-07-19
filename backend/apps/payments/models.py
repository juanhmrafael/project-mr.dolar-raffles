# backend/apps/payments/models.py
"""
Modelos para la gestión de pagos y su verificación.
"""

import hashlib
from datetime import date

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from utils.enums import CurrencyChoices


class Bank(models.Model):
    """
    Representa una entidad bancaria con su código y nombre.
    """

    code = models.CharField(_("Bank Code"), max_length=4, unique=True)
    name = models.CharField(_("Bank Name"), max_length=100)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Bank")
        verbose_name_plural = _("Banks")
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class PaymentMethod(models.Model):
    """
    Representa una cuenta específica a la que se puede realizar un pago.
    Ej: Una cuenta de Zelle, un Pago Móvil específico, etc.
    """

    METHOD_TYPE_CHOICES = [
        ("PAGO_MOVIL", _("Mobile Payment")),
        ("ZELLE", _("Zelle")),
        ("BINANCE", _("Binance")),
        ("TRANSFERENCIA", _("Bank Transfer")),
    ]

    method_type = models.CharField(
        _("Method Type"), max_length=20, choices=METHOD_TYPE_CHOICES
    )
    name = models.CharField(
        _("Account Nickname"),
        max_length=100,
        help_text=_("E.g., 'Primary Zelle', 'Banesco Mobile Payment'"),
    )
    currency = models.CharField(
        _("Operating Currency"),
        max_length=3,
        choices=CurrencyChoices.choices,  # Usamos la enumeración
        help_text=_("The currency in which transactions are made with this method."),
        editable=False,
    )
    details = models.JSONField(
        _("Account Details"),
        default=dict,
        help_text=_("Account data will be structured here automatically."),
    )

    is_active = models.BooleanField(_("Is Active?"), default=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def is_in_use(self) -> bool:
        """
        Verifica si este método de pago está siendo utilizado activamente.

        Un método de pago se considera "en uso" si está asociado a al menos
        un pago ya registrado o si está seleccionado como método disponible
        en al menos una rifa.

        Returns:
            bool: True si está en uso, False en caso contrario.
        """
        # Usamos .exists() para una consulta de base de datos altamente optimizada.
        # Comprueba si hay algún pago que lo use.
        has_payments = self.payment_set.exists()

        # Comprueba si alguna rifa lo tiene como método disponible.
        # 'raffle_set' es el related_name por defecto para el ManyToManyField.
        # Si lo has cambiado en el modelo Raffle, usa ese nombre.
        is_in_raffles = self.raffle_set.exists()

        return has_payments or is_in_raffles

    def save(self, *args, **kwargs):
        """
        Asigna la moneda automáticamente basado en el tipo de método de pago.
        """
        if self.method_type in ["ZELLE", "BINANCE"]:
            self.currency = CurrencyChoices.USD
        else:  # PAGO_MOVIL, TRANSFERENCIA
            self.currency = CurrencyChoices.VEF
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment methods")


class Payment(models.Model):
    """
    Representa una transacción de pago asociada a una participación.

    Este modelo es crucial para la auditoría financiera. Almacena no solo los
    detalles del pago reportados por el usuario, sino también los valores
    calculados por el sistema (monto esperado, tasa de cambio aplicada)
    en el momento de la transacción.
    """

    STATUS_CHOICES = [
        ("PENDING", _("Pending Verification")),
        ("APPROVED", _("Approved")),
        ("REJECTED", _("Rejected")),
    ]

    participation = models.OneToOneField(
        "participants.Participation",
        on_delete=models.CASCADE,
        related_name="payment",
        verbose_name=_("Participation"),
    )
    payment_method_used = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,  # Proteger para no borrar un método con pagos asociados
        verbose_name=_("Payment Method Used"),
    )

    # --- DATOS DE LA TRANSACCIÓN ---
    transaction_details = models.JSONField(
        _("Transaction Details"),
        help_text=_("Details from the user, e.g., {'reference': '123'}"),
    )
    payment_date = models.DateField(_("Payment Date"), default=date.today)

    # --- Campos calculados por el sistema ---
    # Este es el monto final que el usuario DEBÍA pagar, en la moneda de la transacción.
    amount_to_pay = models.DecimalField(
        _("Amount to Pay"),
        max_digits=12,
        decimal_places=2,
        help_text=_(
            "The final amount the user had to pay, in the currency of the payment method."
        ),
    )

    # --- CAMPOS DE AUDITORÍA Y CONTEXTO ---
    # Congelamos la tasa de cambio usada para el cálculo, si aplica. Es vital para la auditoría.
    exchange_rate_applied = models.DecimalField(
        _("Exchange Rate Applied (VEF per USD)"),
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )
    payment_hash = models.CharField(
        _("Payment Hash"), max_length=64, unique=True, editable=False, db_index=True
    )

    # --- Campos de estado y auditoría ---
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Verified By"),
        related_name="verified_payments",
    )
    verified_at = models.DateTimeField(_("Verified At"), null=True, blank=True)
    verification_notes = models.TextField(_("Verification Notes"), blank=True)

    # --- Campos de Auditoría (Creado/Actualizado) ---
    # ✅ NUEVO: Campo para congelar el precio del ticket
    ticket_price_at_creation = models.DecimalField(
        _("Ticket Price at Creation"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,  # Nullable para migraciones no destructivas
    )
    # ✅ NUEVO: Campo para congelar la cantidad de tickets
    ticket_count_at_creation = models.PositiveIntegerField(
        _("Ticket Count at Creation"), null=True, blank=True
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last Updated At"), auto_now=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-payment_date"]
        indexes = [
            models.Index(fields=["status", "payment_date"]),
        ]

    def __str__(self) -> str:
        return f"Payment for {self.participation} - {self.get_status_display()}"

    def _generate_hash(self) -> str:
        """
        Genera un hash SHA-256 para identificar unívocamente un reporte de pago.

        Usa los datos que un usuario proporciona y que definen unívocamente
        su reporte para evitar duplicados. Ahora incluye el monto para mayor unicidad.

        Returns:
            str: El hash hexadecimal de 64 caracteres.

        Raises:
            ValueError: Si el amount_to_pay no está asignado cuando se llama este método.
        """
        if self.amount_to_pay is None:
            raise ValueError("Cannot generate hash without amount_to_pay.")

        transaction_ref = self.transaction_details.get("reference", "")

        # ✅ NORMALIZACIÓN: Formateamos el decimal a una cadena con 2 decimales.
        amount_str = f"{self.amount_to_pay:.2f}"

        # Concatenamos los campos clave para crear una firma única de la transacción.
        signature = (
            f"{self.payment_method_used.id}:"
            f"{transaction_ref}:"
            f"{self.payment_date.strftime('%Y-%m-%d')}:"
            f"{amount_str}"  # ✅ AÑADIDO
        ).lower()
        return hashlib.sha256(signature.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        """
        Calcula el hash de pago antes de guardar.
        Asegura que el hash solo se calcule una vez.
        """
        # La lógica de asignación del hash se mueve al 'save' del formulario
        # para asegurar que 'amount_to_pay' esté disponible.
        # Mantenemos esta lógica aquí como fallback o si se crea el objeto
        # de forma programática fuera del admin.
        if not self.pk and not self.payment_hash:
            if self.amount_to_pay is not None:
                self.payment_hash = self._generate_hash()
            else:
                # Este caso no debería ocurrir en un flujo normal, pero es una salvaguarda.
                # El hash se generará en un paso posterior si es necesario.
                pass

        super().save(*args, **kwargs)

    @property
    def currency_paid(self) -> str:
        """
        Propiedad derivada que devuelve la moneda de la transacción.
        La única fuente de verdad es el método de pago utilizado.
        """
        if self.payment_method_used:
            return self.payment_method_used.currency
        return ""  # Retorna un string vacío si no hay método de pago asignado
