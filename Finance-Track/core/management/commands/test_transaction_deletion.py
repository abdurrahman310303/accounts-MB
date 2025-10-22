from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Account, Currency, Transaction, Team, Category
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test transaction deletion and account balance reversal functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Transaction Deletion Functionality'))
        
        try:
            # Get or create test user
            user, created = User.objects.get_or_create(
                username='testuser',
                defaults={'email': 'test@example.com'}
            )
            if created:
                self.stdout.write('Created test user')
            
            # Get currencies
            pkr_currency = Currency.objects.get(code='PKR')
            usd_currency = Currency.objects.get(code='USD')
            
            # Create test accounts
            pkr_account, created = Account.objects.get_or_create(
                name='Test PKR Account',
                defaults={
                    'account_type': 'bank',
                    'currency': pkr_currency,
                    'opening_balance': Decimal('10000.00')
                }
            )
            
            usd_account, created = Account.objects.get_or_create(
                name='Test USD Account',
                defaults={
                    'account_type': 'bank',
                    'currency': usd_currency,
                    'opening_balance': Decimal('1000.00')
                }
            )
            
            # Get test category
            try:
                income_category = Category.objects.filter(category_type='income').first()
                expense_category = Category.objects.filter(category_type='expense').first()
            except:
                income_category = None
                expense_category = None
            
            # Record initial balances
            initial_pkr_balance = pkr_account.current_balance
            initial_usd_balance = usd_account.current_balance
            
            self.stdout.write(f'Initial PKR Account Balance: {initial_pkr_balance}')
            self.stdout.write(f'Initial USD Account Balance: {initial_usd_balance}')
            
            # Test 1: Income Transaction
            self.stdout.write('\n--- Testing Income Transaction ---')
            income_transaction = Transaction.objects.create(
                transaction_type='income',
                amount=Decimal('5000.00'),
                currency=pkr_currency,
                exchange_rate_to_pkr=Decimal('1.0000'),
                description='Test Income',
                account=pkr_account,
                category=income_category,
                created_by=user
            )
            
            # Refresh account balance
            pkr_account.refresh_from_db()
            self.stdout.write(f'After Income (+5000): {pkr_account.current_balance}')
            
            # Delete income transaction
            income_transaction.delete()
            pkr_account.refresh_from_db()
            self.stdout.write(f'After Income Deletion: {pkr_account.current_balance}')
            
            # Verify balance is back to initial
            if pkr_account.current_balance == initial_pkr_balance:
                self.stdout.write(self.style.SUCCESS('✓ Income transaction deletion test PASSED'))
            else:
                self.stdout.write(self.style.ERROR('✗ Income transaction deletion test FAILED'))
            
            # Test 2: Expense Transaction
            self.stdout.write('\n--- Testing Expense Transaction ---')
            expense_transaction = Transaction.objects.create(
                transaction_type='expense',
                amount=Decimal('2000.00'),
                currency=pkr_currency,
                exchange_rate_to_pkr=Decimal('1.0000'),
                description='Test Expense',
                account=pkr_account,
                category=expense_category,
                created_by=user
            )
            
            # Refresh account balance
            pkr_account.refresh_from_db()
            self.stdout.write(f'After Expense (-2000): {pkr_account.current_balance}')
            
            # Delete expense transaction
            expense_transaction.delete()
            pkr_account.refresh_from_db()
            self.stdout.write(f'After Expense Deletion: {pkr_account.current_balance}')
            
            # Verify balance is back to initial
            if pkr_account.current_balance == initial_pkr_balance:
                self.stdout.write(self.style.SUCCESS('✓ Expense transaction deletion test PASSED'))
            else:
                self.stdout.write(self.style.ERROR('✗ Expense transaction deletion test FAILED'))
            
            # Test 3: Transfer Transaction (Same Currency)
            self.stdout.write('\n--- Testing Transfer Transaction (Same Currency) ---')
            
            # Create another PKR account for transfer
            pkr_account2, created = Account.objects.get_or_create(
                name='Test PKR Account 2',
                defaults={
                    'account_type': 'cash',
                    'currency': pkr_currency,
                    'opening_balance': Decimal('5000.00')
                }
            )
            
            initial_pkr2_balance = pkr_account2.current_balance
            
            transfer_transaction = Transaction.objects.create(
                transaction_type='transfer',
                amount=Decimal('1500.00'),
                currency=pkr_currency,
                exchange_rate_to_pkr=Decimal('1.0000'),
                description='Test Transfer',
                account=pkr_account,  # From account
                counter_party_account=pkr_account2,  # To account
                created_by=user
            )
            
            # Refresh account balances
            pkr_account.refresh_from_db()
            pkr_account2.refresh_from_db()
            self.stdout.write(f'After Transfer - From Account: {pkr_account.current_balance}')
            self.stdout.write(f'After Transfer - To Account: {pkr_account2.current_balance}')
            
            # Delete transfer transaction
            transfer_transaction.delete()
            pkr_account.refresh_from_db()
            pkr_account2.refresh_from_db()
            self.stdout.write(f'After Transfer Deletion - From Account: {pkr_account.current_balance}')
            self.stdout.write(f'After Transfer Deletion - To Account: {pkr_account2.current_balance}')
            
            # Verify balances are back to initial
            if (pkr_account.current_balance == initial_pkr_balance and 
                pkr_account2.current_balance == initial_pkr2_balance):
                self.stdout.write(self.style.SUCCESS('✓ Transfer transaction deletion test PASSED'))
            else:
                self.stdout.write(self.style.ERROR('✗ Transfer transaction deletion test FAILED'))
            
            # Test 4: Transfer Transaction (Different Currencies)
            self.stdout.write('\n--- Testing Transfer Transaction (Different Currencies) ---')
            
            # Get current USD exchange rate
            usd_rate = usd_currency.exchange_rate_to_pkr
            
            cross_currency_transfer = Transaction.objects.create(
                transaction_type='transfer',
                amount=Decimal('100.00'),  # 100 USD
                currency=usd_currency,
                exchange_rate_to_pkr=usd_rate,
                description='Test Cross-Currency Transfer',
                account=usd_account,  # From USD account
                counter_party_account=pkr_account,  # To PKR account
                created_by=user
            )
            
            # Refresh account balances
            usd_account.refresh_from_db()
            pkr_account.refresh_from_db()
            self.stdout.write(f'After Cross-Currency Transfer - USD Account: {usd_account.current_balance}')
            self.stdout.write(f'After Cross-Currency Transfer - PKR Account: {pkr_account.current_balance}')
            
            # Delete cross-currency transfer transaction
            cross_currency_transfer.delete()
            usd_account.refresh_from_db()
            pkr_account.refresh_from_db()
            self.stdout.write(f'After Cross-Currency Transfer Deletion - USD Account: {usd_account.current_balance}')
            self.stdout.write(f'After Cross-Currency Transfer Deletion - PKR Account: {pkr_account.current_balance}')
            
            # Verify balances are back to initial
            if (usd_account.current_balance == initial_usd_balance and 
                pkr_account.current_balance == initial_pkr_balance):
                self.stdout.write(self.style.SUCCESS('✓ Cross-currency transfer deletion test PASSED'))
            else:
                self.stdout.write(self.style.ERROR('✗ Cross-currency transfer deletion test FAILED'))
            
            self.stdout.write('\n' + self.style.SUCCESS('All transaction deletion tests completed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Test failed with error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
