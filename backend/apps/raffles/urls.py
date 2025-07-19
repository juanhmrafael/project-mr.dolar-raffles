# backend/apps/raffles/urls.py
from django.urls import path

from .views import (
    MainPageAPIView,
    PublicRaffleDetailAPIView,
    RaffleStatsAPIView,
)

app_name = "raffles"

urlpatterns = [
    path("api/v1/main-page/", MainPageAPIView.as_view(), name="api-main-page"),
    path(
        "api/v1/raffles/<slug:slug>/",
        PublicRaffleDetailAPIView.as_view(),
        name="api-raffle-detail",
    ),
    path(
        "api/v1/raffles/<slug:slug>/stats/",
        RaffleStatsAPIView.as_view(),
        name="api-raffle-stats",
    ),
]
