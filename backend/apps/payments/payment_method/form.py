# /apps/payments/payment_method/form.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget
from utils.validators import (
    validate_full_name,
    validate_transaction_payer_id,
    validate_venezuelan_phone,
)

from ..models import Bank, PaymentMethod


class PaymentMethodAdminForm(forms.ModelForm):
    """
    Formulario admin para PaymentMethod que usa campos dinámicos y un widget
    de búsqueda AJAX (Select2) para una mejor UX y un diseño limpio.
    """

    currency_display = forms.CharField(
        label=_("Operating Currency"),
        required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "disabled": "disabled"}),
        help_text=_("The currency in which transactions are made with this method."),
    )

    # --- Campos dinámicos que se mostrarán/ocultarán con JS ---
    custom_phone = forms.CharField(
        label=_("Phone"),
        required=False,
        validators=[validate_venezuelan_phone],
        help_text=_(
            "Enter the 11-digit cell phone number. It will be formatted automatically as (04XX) XXX-XXXX."
        ),
    )

    custom_id_number = forms.CharField(
        label=_("ID Number/RIF"),
        required=False,
        validators=[validate_transaction_payer_id],
        help_text=format_html(
            "{}<br><b>V</b>: Venezolano | <b>E</b>: Extranjero | <b>P</b>: Pasaporte | <b>J</b>: Jurídico | <b>G</b>: Gubernamental | <b>C</b>: Comunal",
            _(
                "Format: L-NNNNNNNN (e.g., V-12345678). It will be formatted automatically."
            ),
        ),
    )

    custom_bank = forms.ModelChoiceField(
        label=_("Bank"),
        queryset=Bank.objects.all(),
        widget=Select2Widget(
            attrs={
                "data-placeholder": _("Selecciona un banco"),
                "data-allow-clear": "true",
                "style": "width: 100%;",
            }
        ),
        required=False,
        empty_label=_("--- Selecciona un banco ---"),
        help_text=_("Select the bank associated with the account."),
    )

    custom_account_number = forms.CharField(
        label=_("Account Number"),
        required=False,
        help_text=_("Enter the full bank account number, typically 20 digits."),
    )

    custom_holder_name = forms.CharField(
        label=_("Holder Name"),
        required=False,
        validators=[validate_full_name],
        help_text=_(
            "Enter the full name of the account holder, at least first and last name."
        ),
    )

    custom_email = forms.EmailField(
        label=_("Email"),
        required=False,
        help_text=_(
            "Enter a valid email address for the account holder (e.g., for Zelle)."
        ),
    )

    custom_pay_id = forms.CharField(
        label=_("Pay ID"),
        required=False,
        help_text=_("Enter the Binance Pay ID associated with the account."),
    )

    class Meta:
        model = PaymentMethod
        exclude = ("details", "currency")

    def __init__(self, *args, **kwargs):
        """
        Pre-rellena los campos 'custom' y los deshabilita si la instancia está en uso.
        """
        super().__init__(*args, **kwargs)

        is_in_use = self.instance and self.instance.pk and self.instance.is_in_use()

        if is_in_use:
            # Deshabilitamos los campos que no deben ser modificados.
            self.fields["method_type"].disabled = True

            # Deshabilitamos todos los campos virtuales 'custom_*'
            for field_name in self.fields:
                if field_name.startswith("custom_"):
                    self.fields[field_name].disabled = True

        # La lógica para pre-rellenar los campos con los valores iniciales se mantiene.
        if self.instance and self.instance.pk and self.instance.details:
            details = self.instance.details
            for key, value in details.items():
                field_name = f"custom_{key}"
                if field_name in self.fields:
                    if key == "bank" and value:
                        try:
                            self.initial[field_name] = Bank.objects.get(code=value)
                        except Bank.DoesNotExist:
                            self.initial[field_name] = None
                    else:
                        self.initial[field_name] = value

    def clean(self):
        """
        Valida los datos y construye el JSON 'details' basado en los campos
        relevantes para el 'method_type' seleccionado.
        Aquí reside la lógica de negocio y la validación de integridad.
        """
        cleaned_data = super().clean()
        
        is_in_use = self.instance and self.instance.pk and self.instance.is_in_use()

        # Si el método está en uso, los campos críticos no vienen en el POST
        # porque estaban deshabilitados. No intentamos procesarlos.
        # Los únicos campos en 'cleaned_data' serán 'name' y 'is_active', que es lo correcto.
        if is_in_use:
            return cleaned_data

        # La lógica de validación y construcción de 'details' solo se ejecuta
        # si el objeto es nuevo o no está en uso.
        method_type = cleaned_data.get("method_type")
        details = {}
        errors = {}

        # Mapeo de tipos de método a sus campos y validadores requeridos
        FIELD_MAP = {
            "PAGO_MOVIL": ["phone", "id_number", "bank"],
            "TRANSFERENCIA": ["account_number", "holder_name", "id_number", "bank"],
            "ZELLE": ["email", "holder_name"],
            "BINANCE": ["pay_id", "holder_name"],
        }

        required_fields = FIELD_MAP.get(method_type, [])
        for field_key in required_fields:
            field_name = f"custom_{field_key}"
            field_value = cleaned_data.get(field_name)

            if not field_value:
                # ✅ Validación de requeridos: Error más específico
                errors[field_name] = ValidationError(
                    _("This field is required for the selected payment method."),
                    code="required",
                )
                continue

            # Construimos el diccionario 'details'
            if field_key == "bank" and isinstance(field_value, Bank):
                details[field_key] = field_value.code
            else:
                details[field_key] = field_value

        if errors:
            raise ValidationError(errors)

        cleaned_data["details"] = details
        return cleaned_data

    def save(self, commit=True):
        """
        Sobrescribe el método save para asignar 'details' desde los datos limpios,
        solo si no estamos en modo de solo lectura.
        """
        is_in_use = self.instance and self.instance.pk and self.instance.is_in_use()

        # Solo modificamos 'details' si NO está en uso.
        if not is_in_use:
            self.instance.details = self.cleaned_data.get("details", {})

        # Django es lo suficientemente inteligente como para no modificar los campos
        # que estaban deshabilitados en el formulario.
        return super().save(commit)