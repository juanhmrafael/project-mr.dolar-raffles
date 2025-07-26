# backend/utils/validators.py
"""
Validadores personalizados para los modelos de la app 'users'.

Este módulo centraliza la lógica de validación, promoviendo la reutilización (DRY)
y la facilidad de mantenimiento.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def _validate_base_id_format(value: str, allowed_prefixes: str, error_message: str):
    """
    Función auxiliar privada para validar la estructura base de un ID.

    Args:
        value (str): El valor del ID a validar.
        allowed_prefixes (str): Una cadena de caracteres con los prefijos permitidos (ej: "VEP").
        error_message (str): El mensaje de error a mostrar si la validación falla.
    """
    # Construimos la expresión regular dinámicamente.
    # Ej: si allowed_prefixes es "VEP", el regex será ^[VEP]-\d{7,9}$
    regex = f"^[{allowed_prefixes.upper()}]-\\d{{7,}}$"

    if not re.match(regex, value.upper()):
        raise ValidationError(error_message)


def validate_natural_person_id(value: str):
    """
    Valida un ID para una PERSONA NATURAL (ej: para un registro de usuario).

    - Propósito: Identificar a un individuo.
    - Prefijos Permitidos: V (Venezolano), E (Extranjero), P (Pasaporte).
    - Formato Esperado: L-NNNNNNNN (ej: V-12345678).

    Args:
        value (str): El valor a validar.

    Raises:
        ValidationError: Si el valor no es un ID de persona natural válido.
    """
    allowed_prefixes = "VEP"
    error_message = _(
        "Invalid ID. Must be a valid personal ID (V, E, P) like 'V-12345678'."
    )
    _validate_base_id_format(value, allowed_prefixes, error_message)


def validate_transaction_payer_id(value: str):
    """
    Valida un ID para un PAGADOR en una transacción (ej: Pago Móvil).

    - Propósito: Identificar al emisor de un pago, que puede ser una persona o una entidad.
    - Prefijos Permitidos: Todos (V, E, P, J, G, C).
    - Formato Esperado: L-NNNNNNNN (ej: V-12345678, J-123456789).

    Args:
        value (str): El valor a validar.

    Raises:
        ValidationError: Si el valor no es un ID de pagador válido.
    """
    allowed_prefixes = "VEPJGC"
    error_message = _(
        "Invalid Payer ID format. Use a format like 'V-12345678' or 'J-123456789'."
    )
    _validate_base_id_format(value, allowed_prefixes, error_message)


def validate_venezuelan_phone(value: str):
    """
    Valida un número de teléfono celular venezolano.
    Formato esperado: (04XX) YYY-YYYY (ej: (0414) 123-4567)
    """
    # Expresión regular para formato: ^\(0(412|...)\)\s\d{3}-\d{4}$
    # ^      -> Inicio
    # \(     -> Paréntesis literal de apertura
    # 0(412|422|414|424|416|426) -> Códigos de operadora válidos
    # \)     -> Paréntesis literal de cierre
    # \s     -> Un espacio
    # \d{3}-\d{4} -> 3 dígitos, guión, 4 dígitos
    # $      -> Fin
    regex = r"^\(0(412|422|414|424|416|426)\)\s\d{3}-\d{4}$"
    if not re.match(regex, value):
        raise ValidationError(
            _(
                "Invalid phone number. Must be a valid Venezuelan cell number (e.g., (04XX) XXX-XXXX)."
            )
        )


def validate_full_name(value: str):
    """
    Valida que un nombre completo no contenga números o caracteres extraños.
    Permite letras (incluyendo acentos), espacios y apóstrofes.
    """
    # Permite letras de varios idiomas, espacios, y apóstrofes.
    regex = r"^[a-zA-Z\sáéíóúÁÉÍÓÚñÑ']+$"
    if not re.match(regex, value):
        raise ValidationError(_("Name can only contain letters and spaces."))

    if len(value.strip().split()) < 2:
        raise ValidationError(_("Please provide at least a first and last name."))
