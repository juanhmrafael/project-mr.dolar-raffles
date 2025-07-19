# backend/apps/participants/urls.py
from django.urls import path

from .views import CreateParticipationAPIView, TicketLookupAPIView

app_name = "participants"

urlpatterns = [
    path(
        "api/v1/participations/",
        CreateParticipationAPIView.as_view(),
        name="api-create-participation",
    ),
    path(
        "api/v1/tickets/lookup/",
        TicketLookupAPIView.as_view(),
        name="api-ticket-lookup",
    ),
]
