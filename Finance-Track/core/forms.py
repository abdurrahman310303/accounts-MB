from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Transaction, Account, Category, Team, Currency


class TransactionForm(forms.ModelForm):
    # Add counter party account field for transfers
    counter_party_account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True),
        required=False,
        empty_label="Select Counter Party Account",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Add subcategory field for expense transactions
    subcategory = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="Select Subcategory",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Subcategory (shown for expense transactions only)"
    )
    
    # Exchange rate fields for currency conversion
    exchange_rate_to_pkr = forms.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.0001',
            'placeholder': 'Exchange rate to PKR'
        }),
        help_text="Exchange rate from transaction currency to PKR"
    )
    
    counter_party_exchange_rate = forms.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.0001',
            'placeholder': 'Counter party exchange rate'
        }),
        help_text="Exchange rate from counter party currency to PKR"
    )
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_type', 'amount', 'description', 'transaction_date',
            'team', 'account', 'category', 'counter_party_account', 
            'exchange_rate_to_pkr', 'counter_party_exchange_rate'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter transaction description'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'team': forms.Select(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set up teams - allow all teams, not just user teams
        all_teams = Team.objects.all()
        self.fields['team'].queryset = all_teams
            
        # Set up accounts - all active accounts
        active_accounts = Account.objects.filter(is_active=True)
        self.fields['account'].queryset = active_accounts
        self.fields['counter_party_account'].queryset = active_accounts
        
        # Set up categories - only main categories (parent categories), will be filtered by JS
        self.fields['category'].queryset = Category.objects.filter(
            parent__isnull=True,  # Only main/parent categories
            is_active=True
        ).order_by('category_type', 'name')
        
        # Set up subcategories - will be dynamically populated by JavaScript
        self.fields['subcategory'].queryset = Category.objects.filter(
            parent__isnull=False,  # Only subcategories
            is_active=True
        ).order_by('name')
        
        # Set field properties
        self.fields['team'].required = False  # Will be set conditionally via JavaScript
        self.fields['account'].required = True
        self.fields['category'].required = False  # Will be set conditionally via JavaScript
        self.fields['subcategory'].required = False  # Only required for expense
        self.fields['counter_party_account'].required = False  # Will be set conditionally via JavaScript
        
        # Add empty labels
        self.fields['account'].empty_label = "Select Account"
        self.fields['category'].empty_label = "Select Category"
        self.fields['team'].empty_label = "Select Team"

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        account = cleaned_data.get('account')
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')
        counter_party_account = cleaned_data.get('counter_party_account')
        team = cleaned_data.get('team')
        exchange_rate_to_pkr = cleaned_data.get('exchange_rate_to_pkr')
        counter_party_exchange_rate = cleaned_data.get('counter_party_exchange_rate')

        if transaction_type == 'income':
            # For income transactions
            if not account:
                raise forms.ValidationError('Account is required for income transactions.')
            if not category:
                raise forms.ValidationError('Category is required for income transactions.')
            if not team:
                raise forms.ValidationError('Team is required for income transactions.')
            
            # Check if category type matches transaction type
            if category and category.category_type != transaction_type:
                raise forms.ValidationError(f'Category must be of type {transaction_type}.')
            
            # For income, the final category is the main category (no subcategory)
            cleaned_data['category'] = category
            
            # Check exchange rate for non-PKR accounts
            if account and account.currency.code != 'PKR':
                if not exchange_rate_to_pkr:
                    raise forms.ValidationError(f'Exchange rate to PKR is required for {account.currency.code} transactions.')
                if exchange_rate_to_pkr <= 0:
                    raise forms.ValidationError('Exchange rate must be greater than 0.')
            else:
                # For PKR accounts, set rate to 1
                cleaned_data['exchange_rate_to_pkr'] = 1.0000
        
        elif transaction_type == 'expense':
            # For expense transactions
            if not account:
                raise forms.ValidationError('Account is required for expense transactions.')
            if not category:
                raise forms.ValidationError('Category is required for expense transactions.')
            if not subcategory:
                raise forms.ValidationError('Subcategory is required for expense transactions.')
            if not team:
                raise forms.ValidationError('Team is required for expense transactions.')
            
            # Check if category type matches transaction type
            if category and category.category_type != transaction_type:
                raise forms.ValidationError(f'Category must be of type {transaction_type}.')
            
            # Check if subcategory belongs to the selected category
            if subcategory and subcategory.parent != category:
                raise forms.ValidationError('Subcategory must belong to the selected category.')
            
            # For expense, the final category is the subcategory
            cleaned_data['category'] = subcategory
            
            # Check exchange rate for non-PKR accounts
            if account and account.currency.code != 'PKR':
                if not exchange_rate_to_pkr:
                    raise forms.ValidationError(f'Exchange rate to PKR is required for {account.currency.code} transactions.')
                if exchange_rate_to_pkr <= 0:
                    raise forms.ValidationError('Exchange rate must be greater than 0.')
            else:
                # For PKR accounts, set rate to 1
                cleaned_data['exchange_rate_to_pkr'] = 1.0000
        
        elif transaction_type == 'owners_equity':
            # For owners equity transactions
            if not account:
                raise forms.ValidationError('Account is required for owners equity transactions.')
            if not category:
                raise forms.ValidationError('Category is required for owners equity transactions.')
            # Team is NOT required for owners equity
            
            # Check if category type matches transaction type
            if category and category.category_type != transaction_type:
                raise forms.ValidationError(f'Category must be of type {transaction_type}.')
            
            # For owners equity, the final category is the main category (no subcategory)
            cleaned_data['category'] = category
            
            # Check exchange rate for non-PKR accounts
            if account and account.currency.code != 'PKR':
                if not exchange_rate_to_pkr:
                    raise forms.ValidationError(f'Exchange rate to PKR is required for {account.currency.code} transactions.')
                if exchange_rate_to_pkr <= 0:
                    raise forms.ValidationError('Exchange rate must be greater than 0.')
            else:
                # For PKR accounts, set rate to 1
                cleaned_data['exchange_rate_to_pkr'] = 1.0000

        elif transaction_type == 'transfer':
            # For transfer transactions
            if not account:
                raise forms.ValidationError('From account is required for transfer transactions.')
            if not counter_party_account:
                raise forms.ValidationError('Counter party account is required for transfer transactions.')
            if account == counter_party_account:
                raise forms.ValidationError('From and counter party accounts cannot be the same.')
            
            # Smart exchange rate handling for transfers
            from_currency = account.currency.code
            to_currency = counter_party_account.currency.code
            
            if from_currency == 'PKR' and to_currency == 'PKR':
                # PKR to PKR - no exchange rate needed
                cleaned_data['exchange_rate_to_pkr'] = 1.0000
                cleaned_data['counter_party_exchange_rate'] = 1.0000
                
            elif from_currency == 'PKR' and to_currency != 'PKR':
                # PKR to foreign currency (e.g., PKR to USD)
                cleaned_data['exchange_rate_to_pkr'] = 1.0000  # PKR source account
                
                if not counter_party_exchange_rate:
                    raise forms.ValidationError(f'Exchange rate to PKR is required for converting to {to_currency}. Enter: 1 {to_currency} = X PKR')
                if counter_party_exchange_rate <= 0:
                    raise forms.ValidationError('Exchange rate must be greater than 0.')
                # counter_party_exchange_rate is already set
                
            elif from_currency != 'PKR' and to_currency == 'PKR':
                # Foreign currency to PKR (e.g., USD to PKR)
                cleaned_data['counter_party_exchange_rate'] = 1.0000  # PKR destination account
                
                if not exchange_rate_to_pkr:
                    raise forms.ValidationError(f'Exchange rate to PKR is required for converting from {from_currency}. Enter: 1 {from_currency} = X PKR')
                if exchange_rate_to_pkr <= 0:
                    raise forms.ValidationError('Exchange rate must be greater than 0.')
                # exchange_rate_to_pkr is already set
                
            elif from_currency != 'PKR' and to_currency != 'PKR':
                # Foreign currency to foreign currency (e.g., USD to USD or USD to GBP)
                if from_currency == to_currency:
                    # Same foreign currency (e.g., USD to USD)
                    if not exchange_rate_to_pkr:
                        # Use current exchange rate from currency model
                        cleaned_data['exchange_rate_to_pkr'] = account.currency.exchange_rate_to_pkr
                        cleaned_data['counter_party_exchange_rate'] = counter_party_account.currency.exchange_rate_to_pkr
                    else:
                        # User provided rate
                        if exchange_rate_to_pkr <= 0:
                            raise forms.ValidationError('Exchange rate must be greater than 0.')
                        cleaned_data['counter_party_exchange_rate'] = exchange_rate_to_pkr
                else:
                    # Different foreign currencies (e.g., USD to GBP)
                    if not exchange_rate_to_pkr:
                        raise forms.ValidationError(f'Exchange rate to PKR is required for {from_currency} account.')
                    if not counter_party_exchange_rate:
                        raise forms.ValidationError(f'Exchange rate to PKR is required for {to_currency} account.')
                    if exchange_rate_to_pkr <= 0 or counter_party_exchange_rate <= 0:
                        raise forms.ValidationError('Exchange rates must be greater than 0.')
            
            # Team is not required for transfers

        return cleaned_data

    def clean_transaction_date(self):
        """Ensure transaction_date is valid"""
        transaction_date = self.cleaned_data.get('transaction_date')
        # DateField returns datetime.date object, which doesn't need timezone handling
        # Just return the date as is
        return transaction_date

    def save(self, commit=True):
        from decimal import Decimal
        
        instance = super().save(commit=False)
        
        # Set exchange rates from form
        instance.exchange_rate_to_pkr = self.cleaned_data.get('exchange_rate_to_pkr')
        instance.counter_party_exchange_rate = self.cleaned_data.get('counter_party_exchange_rate')
        
        # Handle transfer transactions
        if instance.transaction_type == 'transfer':
            instance.counter_party_account = self.cleaned_data['counter_party_account']
            instance.category = None  # No category for transfers
            instance.team = None  # No team for transfers
        
        # Set currency and exchange rate based on account
        if instance.account:
            instance.currency = instance.account.currency
            if not instance.exchange_rate_to_pkr:
                instance.exchange_rate_to_pkr = instance.account.currency.exchange_rate_to_pkr
        
        # Ensure amount_pkr is calculated - convert to Decimal for proper arithmetic
        if instance.currency and instance.exchange_rate_to_pkr:
            amount_decimal = Decimal(str(instance.amount))
            rate_decimal = Decimal(str(instance.exchange_rate_to_pkr))
            instance.amount_pkr = amount_decimal * rate_decimal
        else:
            instance.amount_pkr = Decimal(str(instance.amount))  # Default to PKR
        
        if commit:
            instance.save()
        return instance


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'currency', 'opening_balance', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'opening_balance': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Add help text for opening balance
        self.fields['opening_balance'].help_text = "The initial balance when creating this account"


class CategoryForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="None (Main Category)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select a parent category to create a subcategory (only for expense categories)"
    )
    
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'parent', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        # If editing an existing category, exclude it and its descendants from parent choices
        if self.instance and self.instance.pk:
            # Only allow parent selection for expense categories
            if self.instance.category_type == 'expense':
                # Get all descendants to exclude
                descendants = self.get_descendants(self.instance)
                excluded_ids = [self.instance.pk] + [d.pk for d in descendants]
                
                # Filter parent choices by category type and exclude self and descendants
                self.fields['parent'].queryset = Category.objects.filter(
                    category_type='expense',
                    is_active=True
                ).exclude(pk__in=excluded_ids).order_by('parent__name', 'name')
            else:
                # For income and transfer, disable parent field
                self.fields['parent'].queryset = Category.objects.none()
                self.fields['parent'].widget.attrs['disabled'] = True
                self.fields['parent'].help_text = "Subcategories are only available for expense categories"
        else:
            # For new categories, only show expense categories as parent options
            self.fields['parent'].queryset = Category.objects.filter(
                category_type='expense',
                is_active=True
            ).order_by('parent__name', 'name')
    
    def get_descendants(self, category):
        """Recursively get all descendants of a category"""
        descendants = []
        for child in category.subcategories.all():
            descendants.append(child)
            descendants.extend(self.get_descendants(child))
        return descendants
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        category_type = cleaned_data.get('category_type')
        
        # Only expense categories can have parents (subcategories)
        if parent and category_type != 'expense':
            raise forms.ValidationError(
                'Only expense categories can have subcategories. Income, transfer, and owners equity categories cannot have parent categories.'
            )
        
        # If parent is selected, ensure category types match
        if parent and parent.category_type != category_type:
            raise forms.ValidationError(
                f'Parent category type ({parent.get_category_type_display()}) must match '
                f'this category type ({dict(Category.CATEGORY_TYPES)[category_type]}).'
            )
        
        return cleaned_data

    def save(self, commit=True):
        category = super().save(commit=False)
        
        # Only auto-assign parent for expense categories if no parent is selected
        if not category.parent and category.category_type == 'expense':
            # Check if a main category already exists for expense type
            main_category_exists = Category.objects.filter(
                category_type='expense',
                parent=None
            ).exclude(pk=category.pk if category.pk else None).exists()
            
            if main_category_exists and category.pk is None:
                # If creating new expense and main exists, find it and set as parent
                try:
                    main_category = Category.objects.get(
                        category_type='expense',
                        parent=None
                    )
                    category.parent = main_category
                except Category.MultipleObjectsReturned:
                    # If multiple main categories exist, use the first one
                    main_category = Category.objects.filter(
                        category_type='expense',
                        parent=None
                    ).first()
                    category.parent = main_category
        
        # For income and transfer categories, never auto-assign parent
        # They should always be main categories (parent=None)
        
        if commit:
            category.save()
        return category


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Add help text
        self.fields['name'].help_text = "Enter a unique team name"
        self.fields['description'].help_text = "Optional: Describe the team's purpose"
