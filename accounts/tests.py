from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import BankAccount


User = get_user_model()


class BankAccountBalanceTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='balance_customer',
            email='balance@example.com',
            password='StrongPass123!Secure',
        )

        self.other_customer = User.objects.create_user(
            username='other_balance_customer',
            email='otherbalance@example.com',
            password='OtherPass123!Secure',
        )

        self.account = BankAccount.objects.create(
            owner=self.customer,
            account_type=BankAccount.AccountType.SAVINGS,
            balance=Decimal('1250.50'),
        )

        self.other_account = BankAccount.objects.create(
            owner=self.other_customer,
            account_type=BankAccount.AccountType.CURRENT,
            balance=Decimal('800.00'),
        )

        self.balance_url = (
            f'/api/accounts/{self.account.pk}/balance/'
        )

    def test_customer_can_view_own_balance(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.balance_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data['account_id'],
            self.account.id,
        )
        self.assertEqual(
            response.data['account_number'],
            self.account.account_number,
        )
        self.assertEqual(
            response.data['balance'],
            Decimal('1250.50'),
        )

    def test_customer_cannot_view_another_customers_balance(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(
            f'/api/accounts/{self.other_account.pk}/balance/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_balance_endpoint_requires_authentication(self):
        response = self.client.get(self.balance_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
