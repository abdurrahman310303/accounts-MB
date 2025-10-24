from django.contrib import admin
from .models import Team, Currency, Category, Account, Transaction, TransactionAttachment


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['members']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'exchange_rate_to_pkr', 'is_active']
    list_filter = ['is_active']
    list_editable = ['exchange_rate_to_pkr', 'is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'parent', 'is_active']
    list_filter = ['category_type', 'parent', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'currency', 'opening_balance', 'current_balance', 'current_balance_pkr', 'is_active']
    list_filter = ['account_type', 'currency', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['opening_balance_pkr', 'current_balance', 'current_balance_pkr']
    list_editable = ['is_active']


class TransactionAttachmentInline(admin.TabularInline):
    model = TransactionAttachment
    extra = 0


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['description', 'transaction_type', 'amount', 'amount_pkr', 'account', 'team', 'transaction_date']
    list_filter = ['transaction_type', 'team', 'transaction_date', 'category']
    search_fields = ['description', 'notes']
    readonly_fields = ['amount_pkr']
    date_hierarchy = 'transaction_date'
    inlines = [TransactionAttachmentInline]
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Show/hide fields based on transaction type
        if obj and obj.transaction_type == 'transfer':
            # For transfers, hide category and team (show account and counter_party_account)
            if 'category' in form.base_fields:
                form.base_fields['category'].widget.attrs['style'] = 'display:none;'
            if 'team' in form.base_fields:
                form.base_fields['team'].widget.attrs['style'] = 'display:none;'
        else:
            # For income/expense/owners_equity, hide counter_party_account
            if 'counter_party_account' in form.base_fields:
                form.base_fields['counter_party_account'].widget.attrs['style'] = 'display:none;'
        
        return form
