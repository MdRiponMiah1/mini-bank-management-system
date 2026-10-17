import secrets

from django.conf import settings
from django.db import models


def generate_account_number():
    """
    Generate a unique 12-digit bank account number.
    """
    while True:
        account_number = ''.join(
            secrets.choice('0123456789') for _ in range(12)
        )

        if not BankAccount.objects.filter(
            account_number=account_number
        ).exists():
            return account_number


class BankAccount(models.Model):
    class AccountType(models.TextChoices):
        SAVINGS = 'SAVINGS', 'Savings'
        CURRENT = 'CURRENT', 'Current'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
    )

    account_number = models.CharField(
        max_length=12,
        unique=True,
        default=generate_account_number,
        editable=False,
    )

    account_type = models.CharField(
        max_length=10,
        choices=AccountType.choices,
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.account_number} - {self.get_account_type_display()}'
