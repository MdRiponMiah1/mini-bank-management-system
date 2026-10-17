import uuid

from django.core.validators import MinValueValidator
from django.db import models

from accounts.models import BankAccount


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        TRANSFER_SENT = 'TRANSFER_SENT', 'Transfer Sent'
        TRANSFER_RECEIVED = 'TRANSFER_RECEIVED', 'Transfer Received'

    account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='transactions',
    )

    related_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='related_transactions',
        null=True,
        blank=True,
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    reference = models.UUIDField(
        default=uuid.uuid4,
        db_index=True,
        editable=False,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['account', '-created_at'],
                name='txn_account_date_idx',
            ),
            models.Index(
                fields=['transaction_type', '-created_at'],
                name='txn_type_date_idx',
            ),
        ]

    def __str__(self):
        return (
            f'{self.get_transaction_type_display()} - '
            f'{self.amount} - {self.reference}'
        )
