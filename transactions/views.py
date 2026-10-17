import csv
import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from accounts.models import BankAccount
from .models import Transaction
from .serializers import (
    DepositRequestSerializer,
    WithdrawalRequestSerializer,
    TransferRequestSerializer,
    TransactionSerializer,
)


def get_owned_account(user, account_id):
    """
    Return an account belonging to the current user.
    Staff users can access accounts for administrative purposes.
    """
    accounts = BankAccount.objects.all()

    if not user.is_staff:
        accounts = accounts.filter(owner=user)

    return get_object_or_404(accounts, pk=account_id)


def validate_active_account(account):
    if not account.is_active:
        raise ValidationError(
            {'account': 'This bank account is inactive.'}
        )


def transaction_response(message, records, account=None):
    data = {
        'message': message,
        'transactions': TransactionSerializer(
            records,
            many=True,
        ).data,
    }

    if account is not None:
        data['balance'] = str(account.balance)

    return data


class DepositView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account_id = serializer.validated_data['account_id']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data['description']

        with transaction.atomic():
            account = get_owned_account(
                request.user,
                account_id,
            )

            account = BankAccount.objects.select_for_update().get(
                pk=account.pk
            )

            validate_active_account(account)

            account.balance += amount
            account.save(
                update_fields=['balance', 'updated_at']
            )

            record = Transaction.objects.create(
                account=account,
                transaction_type=Transaction.TransactionType.DEPOSIT,
                amount=amount,
                description=description,
            )

        return Response(
            transaction_response(
                'Deposit successful.',
                [record],
                account,
            ),
            status=status.HTTP_201_CREATED,
        )


class WithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account_id = serializer.validated_data['account_id']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data['description']

        daily_limit = Decimal(
            str(
                getattr(
                    settings,
                    'DAILY_WITHDRAWAL_LIMIT',
                    Decimal('50000.00'),
                )
            )
        )

        if amount > daily_limit:
            return Response(
                {
                    'error': (
                        f'The daily withdrawal limit is '
                        f'{daily_limit:.2f}.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            account = get_owned_account(
                request.user,
                account_id,
            )

            account = BankAccount.objects.select_for_update().get(
                pk=account.pk
            )

            validate_active_account(account)

            today = timezone.localdate()

            withdrawn_today = (
                Transaction.objects.filter(
                    account=account,
                    transaction_type=(
                        Transaction.TransactionType.WITHDRAWAL
                    ),
                    created_at__date=today,
                ).aggregate(total=Sum('amount'))['total']
                or Decimal('0.00')
            )

            if withdrawn_today + amount > daily_limit:
                remaining = max(
                    daily_limit - withdrawn_today,
                    Decimal('0.00'),
                )

                return Response(
                    {
                        'error': (
                            'Daily withdrawal limit exceeded.'
                        ),
                        'daily_limit': str(daily_limit),
                        'withdrawn_today': str(withdrawn_today),
                        'remaining_limit': str(remaining),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if account.balance < amount:
                return Response(
                    {
                        'error': 'Insufficient account balance.',
                        'balance': str(account.balance),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            account.balance -= amount
            account.save(
                update_fields=['balance', 'updated_at']
            )

            record = Transaction.objects.create(
                account=account,
                transaction_type=(
                    Transaction.TransactionType.WITHDRAWAL
                ),
                amount=amount,
                description=description,
            )

        return Response(
            transaction_response(
                'Withdrawal successful.',
                [record],
                account,
            ),
            status=status.HTTP_201_CREATED,
        )


class TransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sender_id = serializer.validated_data['from_account_id']
        recipient_number = serializer.validated_data[
            'recipient_account_number'
        ]
        amount = serializer.validated_data['amount']
        description = serializer.validated_data['description']

        with transaction.atomic():
            sender = get_owned_account(
                request.user,
                sender_id,
            )

            recipient = get_object_or_404(
                BankAccount,
                account_number=recipient_number,
            )

            if sender.pk == recipient.pk:
                return Response(
                    {'error': 'You cannot transfer to the same account.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Lock accounts in a consistent order where supported.
            locked_accounts = list(
                BankAccount.objects.select_for_update()
                .filter(pk__in=[sender.pk, recipient.pk])
                .order_by('pk')
            )

            accounts_by_id = {
                account.pk: account
                for account in locked_accounts
            }

            sender = accounts_by_id[sender.pk]
            recipient = accounts_by_id[recipient.pk]

            validate_active_account(sender)
            validate_active_account(recipient)

            if sender.balance < amount:
                return Response(
                    {
                        'error': 'Insufficient account balance.',
                        'balance': str(sender.balance),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sender.balance -= amount
            recipient.balance += amount

            sender.save(
                update_fields=['balance', 'updated_at']
            )
            recipient.save(
                update_fields=['balance', 'updated_at']
            )

            reference = uuid.uuid4()

            sent_record = Transaction.objects.create(
                account=sender,
                related_account=recipient,
                transaction_type=(
                    Transaction.TransactionType.TRANSFER_SENT
                ),
                amount=amount,
                reference=reference,
                description=description or 'Money transfer sent.',
            )

            received_record = Transaction.objects.create(
                account=recipient,
                related_account=sender,
                transaction_type=(
                    Transaction.TransactionType.TRANSFER_RECEIVED
                ),
                amount=amount,
                reference=reference,
                description=description or 'Money transfer received.',
            )

        return Response(
            {
                'message': 'Transfer successful.',
                'reference': str(reference),
                'sender_balance': str(sender.balance),
                'recipient_balance': str(recipient.balance),
                'transactions': TransactionSerializer(
                    [sent_record, received_record],
                    many=True,
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            queryset = Transaction.objects.select_related(
                'account',
                'related_account',
            ).all()
        else:
            queryset = Transaction.objects.select_related(
                'account',
                'related_account',
            ).filter(account__owner=user)

        account_id = self.request.query_params.get('account_id')

        if account_id:
            account = get_owned_account(user, account_id)
            queryset = queryset.filter(account=account)

        transaction_type = self.request.query_params.get('type')

        if transaction_type:
            valid_types = Transaction.TransactionType.values

            if transaction_type not in valid_types:
                raise ValidationError({
                    'type': (
                        'Invalid transaction type. Choose one of: '
                        + ', '.join(valid_types)
                    )
                })

            queryset = queryset.filter(
                transaction_type=transaction_type
            )

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        start = parse_date(start_date) if start_date else None
        end = parse_date(end_date) if end_date else None

        if start_date and start is None:
            raise ValidationError({
                'start_date': 'Use YYYY-MM-DD date format.'
            })

        if end_date and end is None:
            raise ValidationError({
                'end_date': 'Use YYYY-MM-DD date format.'
            })

        if start and end and start > end:
            raise ValidationError({
                'date': 'start_date cannot be after end_date.'
            })

        if start:
            queryset = queryset.filter(
                created_at__date__gte=start
            )

        if end:
            queryset = queryset.filter(
                created_at__date__lte=end
            )

        return queryset


class StatementDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account_id = request.query_params.get('account_id')

        if not account_id:
            raise ValidationError({
                'account_id': 'This query parameter is required.'
            })

        account = get_owned_account(request.user, account_id)

        queryset = Transaction.objects.filter(
            account=account
        ).order_by('created_at')

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        start = parse_date(start_date) if start_date else None
        end = parse_date(end_date) if end_date else None

        if start_date and start is None:
            raise ValidationError({
                'start_date': 'Use YYYY-MM-DD date format.'
            })

        if end_date and end is None:
            raise ValidationError({
                'end_date': 'Use YYYY-MM-DD date format.'
            })

        if start and end and start > end:
            raise ValidationError({
                'date': 'start_date cannot be after end_date.'
            })

        if start:
            queryset = queryset.filter(created_at__date__gte=start)

        if end:
            queryset = queryset.filter(created_at__date__lte=end)

        response = HttpResponse(
            content_type='text/csv; charset=utf-8'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="account_{account.account_number}_statement.csv"'
        )

        # Excel-friendly UTF-8 encoding.
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow([
            'Transaction ID',
            'Type',
            'Amount',
            'Account Number',
            'Related Account Number',
            'Reference',
            'Description',
            'Date and Time',
        ])

        for record in queryset.select_related(
            'account',
            'related_account',
        ):
            writer.writerow([
                record.pk,
                record.get_transaction_type_display(),
                record.amount,
                record.account.account_number,
                (
                    record.related_account.account_number
                    if record.related_account
                    else ''
                ),
                record.reference,
                record.description,
                record.created_at.isoformat(),
            ])

        return response
