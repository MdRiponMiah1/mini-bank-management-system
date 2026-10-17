from rest_framework import serializers

from .models import BankAccount


class BankAccountSerializer(serializers.ModelSerializer):
    account_type_display = serializers.CharField(
        source='get_account_type_display',
        read_only=True,
    )

    class Meta:
        model = BankAccount
        fields = [
            'id',
            'account_number',
            'account_type',
            'account_type_display',
            'balance',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'account_number',
            'balance',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def validate_account_type(self, value):
        allowed_types = [
            BankAccount.AccountType.SAVINGS,
            BankAccount.AccountType.CURRENT,
        ]

        if value not in allowed_types:
            raise serializers.ValidationError(
                'Account type must be SAVINGS or CURRENT.'
            )

        return value
