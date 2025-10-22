from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Team, Currency, Category, Account, Transaction
from datetime import datetime, date
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Import financial data from Excel file to match the existing structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='FinancialTracker_MasterRef__ AbdurRehman.csv',
            help='Excel file path to import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to database'
        )

    def handle(self, *args, **options):
        filename = options['file']
        dry_run = options['dry_run']
        
        if not os.path.exists(filename):
            self.stdout.write(
                self.style.ERROR(f'File {filename} not found')
            )
            return

        try:
            # Read the Excel file
            self.stdout.write(f'Reading Excel file: {filename}')
            
            # Create default user if doesn't exist
            user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@minorbugs.com',
                    'first_name': 'Admin',
                    'last_name': 'User'
                }
            )
            if created:
                user.set_password('admin123')
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            
            # Import Teams
            teams_df = pd.read_excel(filename, sheet_name='Teams')
            self.import_teams(teams_df, user, dry_run)
            
            # Import Categories
            categories_df = pd.read_excel(filename, sheet_name='Categories') 
            self.import_categories(categories_df, dry_run)
            
            # Import Accounts
            accounts_df = pd.read_excel(filename, sheet_name='Accounts')
            self.import_accounts(accounts_df, dry_run)
            
            # Import sample transactions from a few account sheets
            sample_sheets = ['MinorBugsBAHLCurrent', 'Counter', 'SaadMeezan']
            for sheet_name in sample_sheets:
                try:
                    transactions_df = pd.read_excel(filename, sheet_name=sheet_name)
                    self.import_transactions(transactions_df, sheet_name, dry_run)
                except Exception as e:
                    self.stdout.write(f'Could not import {sheet_name}: {e}')
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('Dry run completed - no changes made to database')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Data import completed successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing data: {e}')
            )

    def import_teams(self, df, user, dry_run):
        """Import teams from Teams sheet"""
        self.stdout.write('Importing teams...')
        
        for _, row in df.iterrows():
            team_name = row['Team']
            if pd.isna(team_name):
                continue
                
            if not dry_run:
                team, created = Team.objects.get_or_create(
                    name=team_name,
                    defaults={
                        'description': f'Team {team_name}',
                        'created_by': user
                    }
                )
                team.members.add(user)
                
                if created:
                    self.stdout.write(f'  Created team: {team_name}')
                else:
                    self.stdout.write(f'  Team exists: {team_name}')
            else:
                self.stdout.write(f'  Would create team: {team_name}')

    def import_categories(self, df, dry_run):
        """Import categories from Categories sheet"""
        self.stdout.write('Importing categories...')
        
        # Get all teams for categories (categories can belong to multiple teams)
        if not dry_run:
            teams = Team.objects.all()
            if not teams.exists():
                self.stdout.write('No teams found, skipping categories')
                return
        
        # Comprehensive category mapping based on your Excel data analysis
        category_mapping = {
            # Personal categories (expense type)
            'SaadPersonal': 'expense',
            'KashifPersonal': 'expense', 
            'NasirPersonal': 'expense',
            'HomeExpense': 'expense',
            
            # Business/Office categories (expense type)
            'OfficeRent': 'expense',
            'Equipments': 'expense',
            'CompanyExpense': 'expense',
            'Salaries': 'expense',
            'Repairing': 'expense',
            
            # Marketing categories (expense type)
            'Marketing': 'expense',
            'AdwordUA': 'expense',
            'TikTokUA': 'expense',
            'ApplovinUA': 'expense',
            'UnityUA': 'expense',
            'MarketingMintegral': 'expense',
            
            # Tax categories (expense type)
            'FED': 'expense',
            'ProfitTax': 'expense',
            'Zakat': 'expense',
            
            # Income categories
            'Income': 'income',
            'A/C Receivable': 'income',
            
            # Investment/Other
            'Investments': 'expense',
            'Donation': 'expense',
            
            # Transfer categories (for internal movements)
            'TransferEntry': 'transfer',
            'TransferCredit': 'transfer',
        }
        
        # Create categories for each team
        for _, row in df.iterrows():
            category_name = row['Category']
            if pd.isna(category_name):
                continue
                
            # Determine category type based on mapping
            category_type = category_mapping.get(category_name, 'expense')
            
            # Create description based on category name and type
            if category_type == 'income':
                description = f'Income category: {category_name}'
            elif category_type == 'expense':
                if 'Personal' in category_name:
                    description = f'Personal expense: {category_name}'
                elif any(word in category_name for word in ['Marketing', 'Adword', 'TikTok']):
                    description = f'Marketing expense: {category_name}'
                elif any(word in category_name for word in ['FED', 'Tax', 'Zakat']):
                    description = f'Tax/Fee expense: {category_name}'
                else:
                    description = f'Business expense: {category_name}'
            else:
                description = f'Transfer category: {category_name}'
                
            if not dry_run:
                # Create category for each team (they might use the same categories)
                for team in teams:
                    category, created = Category.objects.get_or_create(
                        name=category_name,
                        team=team,
                        category_type=category_type,
                        defaults={
                            'description': description
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'  Created category: {category_name} ({category_type}) for team {team.name}')
                    else:
                        self.stdout.write(f'  Category exists: {category_name} for team {team.name}')
            else:
                self.stdout.write(f'  Would create category: {category_name} ({category_type}) for all teams')

    def import_accounts(self, df, dry_run):
        """Import accounts from Accounts sheet"""
        self.stdout.write('Importing accounts...')
        
        if not dry_run:
            try:
                minorbugs_team = Team.objects.get(name='MinorBugs')
                usd_currency = Currency.objects.get(code='USD')
                pkr_currency = Currency.objects.get(code='PKR')
            except (Team.DoesNotExist, Currency.DoesNotExist) as e:
                self.stdout.write(f'Required objects not found: {e}')
                return
        
        for _, row in df.iterrows():
            account_name = row['Account']
            default_currency = row['DefaultCurrency']
            
            if pd.isna(account_name) or pd.isna(default_currency):
                continue
            
            # Determine account type based on name
            if 'Retention' in account_name:
                account_type = 'savings'
            elif 'Current' in account_name:
                account_type = 'bank'
            elif 'Saving' in account_name:
                account_type = 'savings'
            elif 'Meezan' in account_name:
                account_type = 'bank'
            elif 'Wise' in account_name:
                account_type = 'bank'
            else:
                account_type = 'cash'
                
            if not dry_run:
                currency = usd_currency if default_currency == 'USD' else pkr_currency
                
                account, created = Account.objects.get_or_create(
                    name=account_name,
                    team=minorbugs_team,
                    defaults={
                        'account_type': account_type,
                        'currency': currency,
                        'balance': 0,
                        'description': f'Account for {account_name}'
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created account: {account_name} ({default_currency})')
                else:
                    self.stdout.write(f'  Account exists: {account_name}')
            else:
                self.stdout.write(f'  Would create account: {account_name} ({default_currency})')

    def import_transactions(self, df, sheet_name, dry_run):
        """Import sample transactions from account sheets"""
        self.stdout.write(f'Importing transactions from {sheet_name}...')
        
        if dry_run:
            non_null_rows = df.dropna(subset=['Amount', 'Description'])
            self.stdout.write(f'  Would import {len(non_null_rows)} transactions from {sheet_name}')
            return
        
        try:
            minorbugs_team = Team.objects.get(name='MinorBugs')
            user = User.objects.get(username='admin')
            
            # Get the account for this sheet
            try:
                account = Account.objects.get(name__icontains=sheet_name.replace('Sheet', ''))
            except Account.DoesNotExist:
                self.stdout.write(f'  Account not found for {sheet_name}')
                return
                
        except (Team.DoesNotExist, User.DoesNotExist) as e:
            self.stdout.write(f'  Required objects not found: {e}')
            return
        
        # Import first few non-null transactions as examples
        count = 0
        for _, row in df.iterrows():
            if count >= 5:  # Limit to first 5 transactions per sheet
                break
                
            amount = row.get('Amount')
            description = row.get('Description')
            category_name = row.get('Category')
            
            if pd.isna(amount) or pd.isna(description):
                continue
                
            # Try to get category
            category = None
            if not pd.isna(category_name):
                try:
                    category = Category.objects.get(name=category_name, team=minorbugs_team)
                except Category.DoesNotExist:
                    pass
            
            # Determine transaction type
            if amount > 0:
                transaction_type = 'income'
            else:
                transaction_type = 'expense'
                amount = abs(amount)
            
            # Create transaction
            Transaction.objects.create(
                transaction_type=transaction_type,
                amount=amount,
                amount_pkr=amount * account.currency.exchange_rate_to_pkr,
                description=str(description)[:255],
                account=account,
                category=category,
                team=minorbugs_team,
                created_by=user,
                transaction_date=datetime.now()
            )
            
            count += 1
            self.stdout.write(f'  Created transaction: {description[:50]}...')
        
        self.stdout.write(f'  Imported {count} transactions from {sheet_name}')
