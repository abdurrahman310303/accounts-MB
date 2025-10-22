from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Account, Transaction, Category, Team, Currency
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Add 100k income transactions to all active accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--amount',
            type=float,
            default=3105000.0,
            help='Amount to add as income (default: 120000)'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='Bulk Income Addition',
            help='Description for the transactions'
        )

    def handle(self, *args, **options):
        amount = Decimal(str(options['amount']))
        description = options['description']
        
        # Get or create necessary objects
        try:
            # Get first user as transaction creator
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found in the system'))
                return
            
            # Get first team
            team = Team.objects.first()
            if not team:
                self.stdout.write(self.style.ERROR('No teams found in the system'))
                return
            # Get income category
            income_category = Category.objects.filter(
                category_type='income',
                parent__isnull=False,
                is_active=True
            ).first()

            if not income_category:
                # Create a basic income category if none exists
                main_income = Category.objects.filter(
                    category_type='income',
                    parent__isnull=True
                ).first()

                if not main_income:
                    main_income = Category.objects.create(
                        name='income',
                        category_type='income',
                        is_main_category=True
                    )

                income_category = Category.objects.create(
                    name='Bulk Income',
                    category_type='income',
                    parent=main_income,
                    is_active=True
                )
            
            # Get all active accounts
            accounts = Account.objects.filter(is_active=True)
            
            if not accounts.exists():
                self.stdout.write(self.style.ERROR('No active accounts found'))
                return
            
            self.stdout.write(f'Found {accounts.count()} active accounts')
            self.stdout.write(f'Adding {amount:,.2f} income to each account...')
            
            created_transactions = []
            
            for account in accounts:
                # Create income transaction
                transaction = Transaction.objects.create(
                    transaction_type='income',
                    description=description,
                    amount=amount,
                    transaction_date=datetime.now().date(),
                    account=account,
                    category=income_category,
                    team=team,
                    currency=account.currency,
                    exchange_rate_to_pkr=account.currency.exchange_rate_to_pkr,
                    created_by=user,
                    notes=f'Bulk income addition via management command'
                )
                
                created_transactions.append(transaction)
                
                # Display transaction info
                self.stdout.write(
                    f'✓ Created transaction {transaction.id}: '
                    f'{amount:,.2f} {account.currency.code} income for {account.name} '
                    f'(PKR equivalent: {transaction.amount_pkr:,.2f})'
                )
            
            # Summary
            total_pkr_added = sum(t.amount_pkr for t in created_transactions)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully created {len(created_transactions)} income transactions!'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Total PKR value added: {total_pkr_added:,.2f} PKR'
                )
            )
            
            # Display account balances after transactions
            self.stdout.write('\nAccount balances after income addition:')
            for account in accounts:
                account.refresh_from_db()
                self.stdout.write(
                    f'- {account.name}: {account.current_balance:,.2f} {account.currency.code} '
                    f'(PKR: {account.current_balance_pkr:,.2f})'
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating transactions: {str(e)}')
            )
