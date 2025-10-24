from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import date
from decimal import Decimal


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='teams', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Currency(models.Model):
    CURRENCY_CHOICES = [
        ('PKR', 'Pakistani Rupee'),
        ('USD', 'US Dollar'),
        ('GBP', 'British Pound'),
    ]
    
    code = models.CharField(max_length=3, choices=CURRENCY_CHOICES, unique=True)
    name = models.CharField(max_length=50)
    exchange_rate_to_pkr = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=1.0000,
        help_text="Exchange rate to convert to PKR (Primary Currency)"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class Category(models.Model):
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
        ('owners_equity', 'Owners Equity'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=15, choices=CATEGORY_TYPES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def is_main_category(self):
        return self.parent is None

    @property 
    def is_subcategory(self):
        return self.parent is not None

    class Meta:
        ordering = ['category_type', 'parent__name', 'name']
        verbose_name_plural = 'Categories'
        unique_together = ['name', 'parent', 'category_type']


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('cash', 'Cash'),
        ('bank', 'Bank Account'),
        ('credit_card', 'Credit Card'),
        ('savings', 'Savings Account'),
        ('investment', 'Investment Account'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    opening_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        help_text="Opening balance when account was created (editable)"
    )
    opening_balance_pkr = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        help_text="Opening balance converted to PKR"
    )
    current_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        help_text="Current balance in account currency (calculated, read-only)"
    )
    current_balance_pkr = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        help_text="Current balance converted to PKR (calculated, read-only)"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Convert opening balance to PKR
        self.opening_balance_pkr = self.opening_balance * Decimal(str(self.currency.exchange_rate_to_pkr))
        
        # If this is a new account, set current balance to opening balance
        if self.pk is None:
            self.current_balance = self.opening_balance
        
        # Convert current balance to PKR
        self.current_balance_pkr = self.current_balance * Decimal(str(self.currency.exchange_rate_to_pkr))
        
        super().save(*args, **kwargs)

    def calculate_current_balance(self):
        """Calculate current balance based on opening balance + transactions"""
        from django.db.models import Sum
        
        # Get all income transactions
        income_total = self.transactions.filter(transaction_type='income').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get all expense transactions  
        expense_total = self.transactions.filter(transaction_type='expense').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get transfer inflows (money coming into this account)
        transfer_in = self.incoming_transfers.aggregate(
            total=Sum('counter_party_amount')
        )['total'] or 0
        
        # Get transfer outflows (money going out of this account)  
        transfer_out = self.transactions.filter(transaction_type='transfer').aggregate(
            total=Sum('amount')  
        )['total'] or 0
        
        # Calculate current balance
        self.current_balance = self.opening_balance + income_total - expense_total + transfer_in - transfer_out
        
        # Update PKR balances with current exchange rate
        current_rate = Decimal(str(self.currency.exchange_rate_to_pkr))
        self.current_balance_pkr = self.current_balance * current_rate
        self.opening_balance_pkr = self.opening_balance * current_rate
        
        return self.current_balance

    def __str__(self):
        return f"{self.name} ({self.currency.code}) - {self.current_balance}"

    class Meta:
        ordering = ['name']


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
        ('owners_equity', 'Owners Equity'),
    ]
    
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    amount_pkr = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount converted to PKR"
    )
    
    # Exchange rate fields for currency conversion tracking
    currency = models.ForeignKey(
        Currency, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Currency used for this transaction"
    )
    exchange_rate_to_pkr = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Exchange rate to PKR used on transaction date"
    )
    
    # For transfer transactions with different currencies
    counter_party_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='counter_party_transactions',
        help_text="Currency of counter party account for transfers"
    )
    counter_party_exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Exchange rate of counter party currency to PKR"
    )
    counter_party_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount credited to counter party account in their currency"
    )
    
    description = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    
    # For income and expense transactions
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='transactions',
        null=True, 
        blank=True
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True
    )
    
    # For transfer transactions - counter party account
    counter_party_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='incoming_transfers', 
        null=True,
        blank=True,
        help_text="Account to which money is transferred"
    )
    
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='transactions',
        null=True,
        blank=True,
        help_text="Team for income/expense transactions (optional for transfers)"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Set currency and exchange rate based on transaction type
        if self.transaction_type == 'transfer':
            # For transfers, use account (from) currency
            if self.account:
                self.currency = self.account.currency
                # Only set exchange rate if not already provided (allow custom rates)
                if not self.exchange_rate_to_pkr:
                    self.exchange_rate_to_pkr = self.currency.exchange_rate_to_pkr
                
                # Set counter party currency info
                if self.counter_party_account:
                    self.counter_party_currency = self.counter_party_account.currency
                    if not self.counter_party_exchange_rate:
                        self.counter_party_exchange_rate = self.counter_party_currency.exchange_rate_to_pkr
        else:
            # For income/expense/owners_equity, use account currency
            if self.account:
                self.currency = self.account.currency
                # Only set exchange rate if not already provided (allow custom rates)
                if not self.exchange_rate_to_pkr:
                    self.exchange_rate_to_pkr = self.currency.exchange_rate_to_pkr
        
        # Convert amount to PKR using stored exchange rate
        if self.currency and self.exchange_rate_to_pkr:
            self.amount_pkr = Decimal(str(self.amount)) * Decimal(str(self.exchange_rate_to_pkr))
        
        # Calculate counter party amount for transfers
        if self.transaction_type == 'transfer' and self.counter_party_account:
            if self.currency != self.counter_party_currency:
                # Convert via PKR using stored exchange rates
                amount_pkr = Decimal(str(self.amount)) * Decimal(str(self.exchange_rate_to_pkr))
                self.counter_party_amount = amount_pkr / Decimal(str(self.counter_party_exchange_rate))
            else:
                # Same currency, same amount
                self.counter_party_amount = self.amount
        
        # Update account balances (only for new transactions)
        is_new_transaction = self.pk is None
        if is_new_transaction:
            if self.transaction_type == 'income':
                self.account.current_balance += self.amount
                self.account.current_balance_pkr = self.account.current_balance * Decimal(str(self.account.currency.exchange_rate_to_pkr))
                self.account.save()
            elif self.transaction_type == 'expense':
                self.account.current_balance -= self.amount
                self.account.current_balance_pkr = self.account.current_balance * Decimal(str(self.account.currency.exchange_rate_to_pkr))
                self.account.save()
            elif self.transaction_type == 'owners_equity':
                # Owners equity deducts from account (like expense)
                self.account.current_balance -= self.amount
                self.account.current_balance_pkr = self.account.current_balance * Decimal(str(self.account.currency.exchange_rate_to_pkr))
                self.account.save()
            elif self.transaction_type == 'transfer':
                if self.account and self.counter_party_account and self.counter_party_amount:
                    # Deduct from source account
                    self.account.current_balance -= self.amount
                    self.account.current_balance_pkr = self.account.current_balance * Decimal(str(self.account.currency.exchange_rate_to_pkr))
                    
                    # Add to destination account
                    self.counter_party_account.current_balance += self.counter_party_amount
                    self.counter_party_account.current_balance_pkr = self.counter_party_account.current_balance * Decimal(str(self.counter_party_account.currency.exchange_rate_to_pkr))
                    
                    self.account.save()
                    self.counter_party_account.save()
        
        super().save(*args, **kwargs)

    def apply_balance_changes(self):
        """Apply balance changes for this transaction - used for edits"""
        if self.transaction_type == 'income':
            self.account.current_balance += self.amount
            self.account.current_balance_pkr = self.account.current_balance * Decimal(str(self.account.currency.exchange_rate_to_pkr))
            self.account.save()
        elif self.transaction_type == 'expense':
            self.account.current_balance -= self.amount
            self.account.current_balance_pkr = self.account.current_balance * Decimal(str(self.account.currency.exchange_rate_to_pkr))
            self.account.save()
        elif self.transaction_type == 'owners_equity':
            # Owners equity deducts from account (like expense)
            self.account.current_balance -= self.amount
            self.account.current_balance_pkr = self.account.current_balance * Decimal(str(self.account.currency.exchange_rate_to_pkr))
            self.account.save()
        elif self.transaction_type == 'transfer':
            if self.account and self.counter_party_account and self.counter_party_amount:
                # Deduct from source account
                self.account.current_balance -= self.amount
                self.account.current_balance_pkr = self.account.current_balance * Decimal(str(self.account.currency.exchange_rate_to_pkr))
                
                # Add to destination account
                self.counter_party_account.current_balance += self.counter_party_amount
                self.counter_party_account.current_balance_pkr = self.counter_party_account.current_balance * Decimal(str(self.counter_party_account.currency.exchange_rate_to_pkr))
                
                self.account.save()
                self.counter_party_account.save()

    def __str__(self):
        if self.transaction_type == 'transfer':
            return f"Transfer: {self.currency.code}{self.amount} from {self.account} to {self.counter_party_account}"
        else:
            return f"{self.get_transaction_type_display()}: {self.currency.code}{self.amount} - {self.description}"
    
    @property
    def amount_in_pkr(self):
        """Get amount in PKR using the stored exchange rate"""
        return self.amount_pkr

    class Meta:
        ordering = ['-transaction_date']


class TransactionAttachment(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='transaction_attachments/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.transaction}"
