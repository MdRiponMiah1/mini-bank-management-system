from django.urls import path

from .views import (
    DepositView,
    WithdrawalView,
    TransferView,
    TransactionHistoryView,
    StatementDownloadView,
)

urlpatterns = [
    path(
        'deposit/',
        DepositView.as_view(),
        name='transaction-deposit',
    ),
    path(
        'withdraw/',
        WithdrawalView.as_view(),
        name='transaction-withdraw',
    ),
    path(
        'transfer/',
        TransferView.as_view(),
        name='transaction-transfer',
    ),
    path(
        '',
        TransactionHistoryView.as_view(),
        name='transaction-history',
    ),
    path(
        'statement/',
        StatementDownloadView.as_view(),
        name='transaction-statement',
    ),
]
