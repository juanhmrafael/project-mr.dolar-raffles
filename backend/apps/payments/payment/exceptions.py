# backend/apps/payments/exceptions.py
"""Excepciones personalizadas para la aplicación de pagos."""


class PaymentException(Exception):
    """Clase base para excepciones de pago."""

    pass


class PaymentCalculationError(PaymentException):
    """Lanzada cuando hay un error al calcular el monto de un pago."""

    pass


class InvalidPaymentMethodError(PaymentException):
    """Lanzada cuando se intenta usar un método de pago no permitido para una rifa."""

    pass


class ExchangeRateUnavailableError(PaymentException):
    """Lanzada cuando se requiere una tasa de cambio pero no se encuentra."""
    pass

class DuplicatePaymentError(PaymentException):
    """Lanzada cuando se intenta reportar un pago que ya existe."""
    pass