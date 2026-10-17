from decimal import Decimal

from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(
        source='account.account_number',
        read_only=True,
    )

    related_account_number = serializers.CharField(
        source='related_account.account_number',
        read_only=True,
        allow_null=True,
    )

    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True,
    )

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_type',
            'transaction_type_display',
            'amount',
            'account',
            'account_number',
            'related_account',
            'related_account_number',
            'reference',
            'description',
            'created_at',
        ]
        read_only_fields = fields


class DepositRequestSerializer(serializers.Serializer):
    account_id = serializers.IntegerField(min_value=1)

    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )

    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default='',
    )


class WithdrawalRequestSerializer(serializers.Serializer):
    account_id = serializers.IntegerField(min_value=1)

    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )

    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default='',
    )


class TransferRequestSerializer(serializers.Serializer):
    from_account_id = serializers.IntegerField(min_value=1)

    recipient_account_number = serializers.RegexField(
        regex=r'^\d{12}$',
        error_messages={
            'invalid': (
                'Recipient account number must contain '
                'exactly 12 digits.'
            ),
        },
    )

    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )

    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default='',
    )
