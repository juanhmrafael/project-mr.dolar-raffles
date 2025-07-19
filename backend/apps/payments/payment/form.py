# backend/apps/payments/payment/form.py
"""
Formulario para la gestión de Pagos en el Admin de Django.

Este módulo define el `PaymentAdminForm`, que sirve como la capa de validación
y preparación de datos para el `PaymentAdmin`. Su diseño sigue los principios de
responsabilidad única, delegando la presentación al `ModelAdmin` y la lógica de
negocio a los servicios.
"""

from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from participants.models import Participation

from ..models import Payment, PaymentMethod
from .exceptions import PaymentCalculationError
from .services_sync import calculate_payment_amount


class PaymentAdminForm(forms.ModelForm):
    """
    Formulario para la creación y edición de Pagos en el admin.

    Responsabilidades clave:
    1.  Definir campos virtuales ('td_*') para recolectar datos de forma estructurada.
    2.  Poblar dinámicamente el `QuerySet` del método de pago.
    3.  Validar los datos requeridos para los campos virtuales en la creación.
    4.  Orquestar el cálculo de campos del sistema antes de guardar.
    """

    # --- Campos Virtuales para Transaction Details ---
    # Definen la interfaz de entrada de datos. El ModelAdmin y JavaScript
    # se encargan de su presentación y visibilidad.
    td_reference = forms.CharField(label=_("Reference Number"), required=False)
    td_email = forms.EmailField(label=_("Sender's Email (Zelle)"), required=False)
    td_binance_pay_id = forms.CharField(label=_("Binance Pay ID"), required=False)

    class Meta:
        """Configuración del Meta del formulario."""

        model = Payment
        exclude = ("transaction_details",)  # Se construye manualmente.

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Inicializador del formulario. Configura el estado inicial de los campos.
        """
        super().__init__(*args, **kwargs)
        self._setup_dynamic_querysets()
        self._populate_initial_data_for_edit()

    # --------------------------------------------------------------------------
    # MÉTODOS DE CONFIGURACIÓN DEL __INIT__
    # --------------------------------------------------------------------------

    def _setup_dynamic_querysets(self) -> None:
        """
        Configura el QuerySet para `payment_method_used` de forma segura,
        filtrando por la rifa de la participación seleccionada.
        """
        if "payment_method_used" not in self.fields:
            return  # El campo es readonly y no está en el formulario.

        participation = self._get_participation_from_context()
        if participation:
            self.fields[
                "payment_method_used"
            ].queryset = participation.raffle.available_payment_methods.all()
        else:
            self.fields["payment_method_used"].queryset = PaymentMethod.objects.none()

    def _populate_initial_data_for_edit(self) -> None:
        """
        Rellena los campos virtuales 'td_*' con datos del JSON `transaction_details`
        cuando se está editando un pago existente.
        """
        if self.instance.pk and self.instance.transaction_details:
            for key, value in self.instance.transaction_details.items():
                field_name = f"td_{key}"
                if field_name in self.fields:
                    self.initial[field_name] = value

    def _get_participation_from_context(self) -> Participation | None:
        """
        Obtiene la instancia de Participation desde el contexto del formulario.
        """
        if self.instance.pk and self.instance.participation:
            return self.instance.participation
        if "participation" in self.data:
            try:
                return Participation.objects.get(pk=int(self.data.get("participation")))
            except (ValueError, TypeError, Participation.DoesNotExist):
                return None
        return None

    # --------------------------------------------------------------------------
    # MÉTODOS DE VALIDACIÓN Y GUARDADO
    # --------------------------------------------------------------------------

    def clean(self) -> dict[str, Any]:
        """
        Método principal de validación.
        """
        cleaned_data = super().clean()

        if self.errors or self.instance.pk:
            return cleaned_data

        # --- Lógica de validación y cálculo solo para la creación ---
        self._validate_required_td_fields(cleaned_data)

        # Adjuntamos datos calculados a cleaned_data para la validación del hash.
        try:
            self._attach_calculated_fields_to_cleaned_data(cleaned_data)
        except PaymentCalculationError as e:
            raise ValidationError(str(e))

        # Finalmente, validamos la unicidad del hash.
        self._validate_payment_hash_uniqueness(cleaned_data)

        return cleaned_data

    def _validate_required_td_fields(self, cleaned_data: dict) -> None:
        """Valida que los campos virtuales requeridos no estén vacíos."""
        payment_method = cleaned_data.get("payment_method_used")
        if not payment_method:
            return

        FIELD_MAP = {
            "PAGO_MOVIL": ("td_reference",),
            "TRANSFERENCIA": ("td_reference",),
            "ZELLE": ("td_reference", "td_email"),
            "BINANCE": ("td_reference", "td_binance_pay_id"),
        }
        required_fields = FIELD_MAP.get(payment_method.method_type, ("td_reference",))

        errors = {
            field_name: ValidationError(
                _("This field is required for the selected payment method."),
                code="required",
            )
            for field_name in required_fields
            if not cleaned_data.get(field_name)
        }
        if errors:
            raise ValidationError(errors)

    def _attach_calculated_fields_to_cleaned_data(self, cleaned_data: dict) -> None:
        """Calcula monto/tasa y los añade a cleaned_data."""
        participation = cleaned_data.get("participation")
        payment_method = cleaned_data.get("payment_method_used")
        payment_date = cleaned_data.get("payment_date")

        if not all((participation, payment_method, payment_date)):
            return

        amount, _, rate = calculate_payment_amount(
            participation, payment_method, payment_date
        )
        cleaned_data["amount_to_pay"] = amount
        cleaned_data["exchange_rate_applied"] = rate

    def _validate_payment_hash_uniqueness(self, cleaned_data: dict) -> None:
        """Genera un hash y comprueba si ya existe, añadiendo los datos a cleaned_data."""
        payment_method = cleaned_data.get("payment_method_used")
        if not payment_method:
            return

        details = {}
        FIELD_MAP = {
            "PAGO_MOVIL": ["reference"],
            "TRANSFERENCIA": ["reference"],
            "ZELLE": ["reference", "email"],
            "BINANCE": ["reference", "binance_pay_id"],
        }
        fields_to_pack = FIELD_MAP.get(payment_method.method_type, [])
        for field_key in fields_to_pack:
            details[field_key] = cleaned_data.get(f"td_{field_key}")

        temp_payment = Payment(
            payment_method_used=payment_method,
            transaction_details=details,
            payment_date=cleaned_data.get("payment_date"),
            amount_to_pay=cleaned_data.get("amount_to_pay"),
        )

        try:
            payment_hash = temp_payment._generate_hash()
            if Payment.objects.filter(payment_hash=payment_hash).exists():
                raise ValidationError(
                    _(
                        "A payment with this exact reference, date, and amount has already been reported."
                    ),
                    code="duplicate_payment_hash",
                )

            # ✅ Guardamos el hash y los details en cleaned_data para que save() los use.
            cleaned_data["payment_hash"] = payment_hash
            cleaned_data["transaction_details"] = details
        except (ValueError, TypeError):
            # Ocurre si falta algún dato para el hash, pero las validaciones anteriores deberían prevenirlo.
            pass

    def save(self, commit: bool = True) -> Payment:
        """
        Asigna los datos desde cleaned_data a la instancia y guarda.
        """
        if not self.instance.pk:
            self.instance.amount_to_pay = self.cleaned_data.get("amount_to_pay")
            self.instance.exchange_rate_applied = self.cleaned_data.get(
                "exchange_rate_applied"
            )
            self.instance.payment_hash = self.cleaned_data.get("payment_hash")

            participation = self.cleaned_data.get("participation")
            if participation:
                self.instance.ticket_price_at_creation = (
                    participation.raffle.ticket_price
                )
                self.instance.ticket_count_at_creation = participation.ticket_count

        # La construcción de 'details' debe ocurrir en ambos casos (crear/editar).
        self.instance.transaction_details = self.cleaned_data.get(
            "transaction_details", self.instance.transaction_details
        )

        return super().save(commit)
