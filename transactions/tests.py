from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import BankAccount
from transactions.models import Transaction


User = get_user_model()


class MiniBankAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = User.objects.create_user(
            username='test_customer',
            email='customer@example.com',
            password='TestPass123!Bank',
        )

        self.recipient = User.objects.create_user(
            username='test_recipient',
            email='recipient@example.com',
            password='TestPass456!Bank',
        )

        self.account = BankAccount.objects.create(
            owner=self.customer,
            account_type=BankAccount.AccountType.SAVINGS,
            balance=Decimal('1000.00'),
        )

        self.recipient_account = BankAccount.objects.create(
            owner=self.recipient,
            account_type=BankAccount.AccountType.SAVINGS,
            balance=Decimal('500.00'),
        )

        self.client.force_authenticate(user=self.customer)

    def test_deposit_increases_balance(self):
        response = self.client.post(
            '/api/transactions/deposit/',
            {
                'account_id': self.account.id,
                'amount': '200.00',
                'description': 'Test deposit',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)

        self.account.refresh_from_db()

        self.assertEqual(
            self.account.balance,
            Decimal('1200.00'),
        )

        self.assertTrue(
            Transaction.objects.filter(
                account=self.account,
                transaction_type=Transaction.TransactionType.DEPOSIT,
                amount=Decimal('200.00'),
            ).exists()
        )

    def test_deposit_rejects_zero_amount(self):
        response = self.client.post(
            '/api/transactions/deposit/',
            {
                'account_id': self.account.id,
                'amount': '0.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

        self.account.refresh_from_db()

        self.assertEqual(
            self.account.balance,
            Decimal('1000.00'),
        )

    def test_withdrawal_decreases_balance(self):
        response = self.client.post(
            '/api/transactions/withdraw/',
            {
                'account_id': self.account.id,
                'amount': '300.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)

        self.account.refresh_from_db()

        self.assertEqual(
            self.account.balance,
            Decimal('700.00'),
        )

    def test_withdrawal_rejects_insufficient_balance(self):
        response = self.client.post(
            '/api/transactions/withdraw/',
            {
                'account_id': self.account.id,
                'amount': '2000.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

        self.account.refresh_from_db()

        self.assertEqual(
            self.account.balance,
            Decimal('1000.00'),
        )

        self.assertFalse(
            Transaction.objects.filter(
                account=self.account,
                transaction_type=(
                    Transaction.TransactionType.WITHDRAWAL
                ),
            ).exists()
        )

    def test_transfer_updates_both_balances(self):
        response = self.client.post(
            '/api/transactions/transfer/',
            {
                'from_account_id': self.account.id,
                'recipient_account_number': (
                    self.recipient_account.account_number
                ),
                'amount': '250.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)

        self.account.refresh_from_db()
        self.recipient_account.refresh_from_db()

        self.assertEqual(
            self.account.balance,
            Decimal('750.00'),
        )

        self.assertEqual(
            self.recipient_account.balance,
            Decimal('750.00'),
        )

        self.assertEqual(
            Transaction.objects.filter(
                reference=response.data['reference']
            ).count(),
            2,
        )

    def test_failed_transfer_does_not_change_balances(self):
        response = self.client.post(
            '/api/transactions/transfer/',
            {
                'from_account_id': self.account.id,
                'recipient_account_number': (
                    self.recipient_account.account_number
                ),
                'amount': '5000.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

        self.account.refresh_from_db()
        self.recipient_account.refresh_from_db()

        self.assertEqual(
            self.account.balance,
            Decimal('1000.00'),
        )

        self.assertEqual(
            self.recipient_account.balance,
            Decimal('500.00'),
        )

        self.assertEqual(Transaction.objects.count(), 0)

    def test_customer_cannot_use_another_customers_account(self):
        response = self.client.post(
            '/api/transactions/deposit/',
            {
                'account_id': self.recipient_account.id,
                'amount': '100.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 404)

        self.recipient_account.refresh_from_db()

        self.assertEqual(
            self.recipient_account.balance,
            Decimal('500.00'),
        )

    def test_transaction_history_shows_own_transactions(self):
        Transaction.objects.create(
            account=self.account,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=Decimal('100.00'),
        )

        Transaction.objects.create(
            account=self.recipient_account,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=Decimal('200.00'),
        )

        response = self.client.get('/api/transactions/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        self.assertEqual(
            response.data['results'][0]['account'],
            self.account.id,
        )

    def test_csv_statement_download(self):
        Transaction.objects.create(
            account=self.account,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=Decimal('100.00'),
        )

        response = self.client.get(
            '/api/transactions/statement/',
            {'account_id': self.account.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn(
            'attachment;',
            response['Content-Disposition'],
        )

        content = response.content.decode('utf-8-sig')

        self.assertIn('Transaction ID', content)
        self.assertIn('100.00', content)

    def test_withdrawal_rejects_amount_above_daily_limit(self):
        response = self.client.post(
            '/api/transactions/withdraw/',
            {
                'account_id': self.account.id,
                'amount': '50000.01',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

        self.account.refresh_from_db()
        self.assertEqual(
            self.account.balance,
            Decimal('1000.00'),
        )

        self.assertFalse(
            Transaction.objects.filter(
                account=self.account,
                transaction_type=(
                    Transaction.TransactionType.WITHDRAWAL
                ),
            ).exists()
        )

    def test_withdrawal_rejects_exceeding_remaining_daily_limit(self):
        self.account.balance = Decimal('60000.00')
        self.account.save(update_fields=['balance'])

        Transaction.objects.create(
            account=self.account,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            amount=Decimal('40000.00'),
        )

        response = self.client.post(
            '/api/transactions/withdraw/',
            {
                'account_id': self.account.id,
                'amount': '15000.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

        self.account.refresh_from_db()
        self.assertEqual(
            self.account.balance,
            Decimal('60000.00'),
        )

    def test_transaction_history_filters_by_date(self):
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        yesterday_transaction = Transaction.objects.create(
            account=self.account,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=Decimal('100.00'),
        )

        today_transaction = Transaction.objects.create(
            account=self.account,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=Decimal('200.00'),
        )

        yesterday_datetime = timezone.make_aware(
            timezone.datetime.combine(
                yesterday,
                timezone.datetime.min.time(),
            )
        )

        today_datetime = timezone.make_aware(
            timezone.datetime.combine(
                today,
                timezone.datetime.min.time(),
            )
        )

        Transaction.objects.filter(
            pk=yesterday_transaction.pk,
        ).update(created_at=yesterday_datetime)

        Transaction.objects.filter(
            pk=today_transaction.pk,
        ).update(created_at=today_datetime)

        response = self.client.get(
            '/api/transactions/',
            {'start_date': today.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['amount'],
            '200.00',
        )
