from django.core.management.base import BaseCommand
from core.models import Currency, Account, Transaction
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test exchange rate updates and balance recalculation'

    def handle(self, *args, **options):
        # Get USD currency and accounts
        try:
            usd_currency = Currency.objects.get(code='USD')
            usd_accounts = Account.objects.filter(currency=usd_currency)[:2]  # Get first 2 USD accounts
            
            self.stdout.write(f'\n=== BEFORE RATE UPDATE ===')
            self.stdout.write(f'USD Rate: {usd_currency.exchange_rate_to_pkr} PKR')
            
            for account in usd_accounts:
                self.stdout.write(
                    f'Account: {account.name}\n'
                    f'  Balance: ${account.current_balance:,.2f} USD\n'
                    f'  PKR: {account.current_balance_pkr:,.2f} PKR'
                )
            
            # Update USD rate (increase by 5 PKR)
            old_rate = usd_currency.exchange_rate_to_pkr
            new_rate = old_rate + Decimal('5.00')
            usd_currency.exchange_rate_to_pkr = new_rate
            usd_currency.save()
            
            # Recalculate balances for USD accounts
            for account in usd_accounts:
                account.calculate_current_balance()
                account.save()
            
            # Update transaction PKR amounts
            transactions = Transaction.objects.filter(currency=usd_currency)[:3]  # First 3 USD transactions
            for transaction in transactions:
                transaction.amount_pkr = transaction.amount * new_rate
                transaction.save(update_fields=['amount_pkr'])
            
            self.stdout.write(f'\n=== AFTER RATE UPDATE ===')
            self.stdout.write(f'USD Rate: {new_rate} PKR (increased by 5.00)')
            
            for account in usd_accounts:
                account.refresh_from_db()
                self.stdout.write(
                    f'Account: {account.name}\n'
                    f'  Balance: ${account.current_balance:,.2f} USD (same)\n'
                    f'  PKR: {account.current_balance_pkr:,.2f} PKR (updated!)'
                )
            
            self.stdout.write(f'\n=== TRANSACTION PKR AMOUNTS ===')
            for transaction in transactions:
                transaction.refresh_from_db()
                self.stdout.write(
                    f'Transaction: ${transaction.amount} USD = {transaction.amount_pkr:,.2f} PKR'
                )
            
            # Restore original rate
            usd_currency.exchange_rate_to_pkr = old_rate
            usd_currency.save()
            
            for account in usd_accounts:
                account.calculate_current_balance()
                account.save()
            
            for transaction in transactions:
                transaction.amount_pkr = transaction.amount * old_rate
                transaction.save(update_fields=['amount_pkr'])
            
            self.stdout.write(f'\n✅ Test completed! Rate restored to {old_rate} PKR')
            
        except Currency.DoesNotExist:
            self.stdout.write(self.style.ERROR('USD currency not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
