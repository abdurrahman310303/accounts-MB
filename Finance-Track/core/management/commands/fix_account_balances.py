from django.core.management.base import BaseCommand
from core.models import Account, Transaction
from decimal import Decimal


class Command(BaseCommand):
    help = 'Recalculate and fix all account balances'

    def handle(self, *args, **options):
        self.stdout.write('Starting account balance recalculation...')
        
        for account in Account.objects.filter(is_active=True):
            old_balance = account.current_balance
            old_balance_pkr = account.current_balance_pkr
            
            # Recalculate balance using the updated method
            new_balance = account.calculate_current_balance()
            account.save()
            
            self.stdout.write(
                f'Account: {account.name} ({account.currency.code})\n'
                f'  Old Balance: {old_balance:,.2f} -> New Balance: {new_balance:,.2f}\n'
                f'  Old PKR: {old_balance_pkr:,.2f} -> New PKR: {account.current_balance_pkr:,.2f}\n'
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully recalculated all account balances!')
        )
