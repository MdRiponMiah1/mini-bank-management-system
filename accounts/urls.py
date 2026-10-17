from django.urls import path

from .views import (
    BankAccountListCreateView,
    BankAccountDetailView,
    BankAccountBalanceView,
)


urlpatterns = [
    path(
        '',
        BankAccountListCreateView.as_view(),
        name='account-list-create',
    ),
    path(
        '<int:pk>/balance/',
        BankAccountBalanceView.as_view(),
        name='account-balance',
    ),
    path(
        '<int:pk>/',
        BankAccountDetailView.as_view(),
        name='account-detail',
    ),
]
