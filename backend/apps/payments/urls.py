# backend/apps/payments/urls.py
"""URLs para la app de pagos."""

from django.urls import path

from .payment.views import (
    CalculatePaymentAmountAPIView,
    PaymentMethodsForParticipationAPIView,
    PublicPaymentCreateAPIView,
)

app_name = "payments"

urlpatterns = [
    path(
        "api/v1/payments/",
        PublicPaymentCreateAPIView.as_view(),
        name="api-public-create-payment",
    ),
    # APIs de Admin (Internas)
    path(
        "payments/api/methods-for-participation/<int:participation_id>/",
        PaymentMethodsForParticipationAPIView.as_view(),
        name="api-methods-for-participation",
    ),
    path(
        "payments/api/calculate-amount/",
        CalculatePaymentAmountAPIView.as_view(),
        name="api-calculate-amount",
    ),
]
