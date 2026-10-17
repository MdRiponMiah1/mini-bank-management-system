from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'transaction_type',
        'amount',
        'account',
        'related_account',
        'reference',
        'created_at',
    )

    list_filter = (
        'transaction_type',
        'created_at',
    )

    search_fields = (
        'reference',
        'account__account_number',
        'related_account__account_number',
        'account__owner__username',
    )

    readonly_fields = (
        'account',
        'related_account',
        'transaction_type',
        'amount',
        'reference',
        'description',
        'created_at',
    )

    list_select_related = (
        'account',
        'related_account',
    )

    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
