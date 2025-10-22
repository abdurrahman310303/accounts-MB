from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Team, Category
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Import categories from Excel file Categories sheet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='FinancialTracker_MasterRef__ AbdurRehman.csv',
            help='Excel file path to import categories from'
        )
        parser.add_argument(
            '--team',
            type=str,
            help='Specific team name to import categories for (default: all teams)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to database'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing categories before importing'
        )

    def handle(self, *args, **options):
        filename = options['file']
        team_name = options['team']
        dry_run = options['dry_run']
        clear_existing = options['clear_existing']
        
        if not os.path.exists(filename):
            self.stdout.write(
                self.style.ERROR(f'File {filename} not found')
            )
            return

        try:
            # Read the Categories sheet
            self.stdout.write(f'Reading categories from: {filename}')
            categories_df = pd.read_excel(filename, sheet_name='Categories')
            
            # Get teams
            if team_name:
                try:
                    teams = [Team.objects.get(name=team_name)]
                    self.stdout.write(f'Importing categories for team: {team_name}')
                except Team.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Team "{team_name}" not found')
                    )
                    return
            else:
                teams = Team.objects.all()
                if not teams.exists():
                    self.stdout.write(
                        self.style.ERROR('No teams found. Please create teams first.')
                    )
                    return
                self.stdout.write(f'Importing categories for {teams.count()} teams')
            
            # Clear existing categories if requested
            if clear_existing and not dry_run:
                for team in teams:
                    deleted_count = Category.objects.filter(team=team).delete()[0]
                    self.stdout.write(f'Cleared {deleted_count} existing categories for {team.name}')
            
            # Smart category mapping based on analysis
            category_intelligence = {
                # Income categories
                'Income': {
                    'type': 'income',
                    'description': 'General income category for revenue, admob, etc.'
                },
                'A/C Receivable': {
                    'type': 'income', 
                    'description': 'Accounts receivable - money owed to company'
                },
                
                # Personal expense categories  
                'SaadPersonal': {
                    'type': 'expense',
                    'description': 'Personal drawings and expenses for Saad'
                },
                'KashifPersonal': {
                    'type': 'expense',
                    'description': 'Personal drawings and expenses for Kashif'
                },
                'NasirPersonal': {
                    'type': 'expense',
                    'description': 'Personal drawings and expenses for Nasir'
                },
                'HomeExpense': {
                    'type': 'expense',
                    'description': 'Home-related expenses (utilities, etc.)'
                },
                
                # Business expense categories
                'OfficeRent': {
                    'type': 'expense',
                    'description': 'Office rental and related costs'
                },
                'Equipments': {
                    'type': 'expense',
                    'description': 'Equipment purchases and maintenance'
                },
                'CompanyExpense': {
                    'type': 'expense',
                    'description': 'General company operational expenses'
                },
                'Salaries': {
                    'type': 'expense',
                    'description': 'Employee salaries and compensation'
                },
                'Repairing': {
                    'type': 'expense',
                    'description': 'Repair and maintenance costs'
                },
                
                # Marketing expense categories
                'Marketing': {
                    'type': 'expense',
                    'description': 'General marketing and advertising expenses'
                },
                'AdwordUA': {
                    'type': 'expense',
                    'description': 'Google AdWords user acquisition campaigns'
                },
                'TikTokUA': {
                    'type': 'expense',
                    'description': 'TikTok user acquisition campaigns'
                },
                'ApplovinUA': {
                    'type': 'expense',
                    'description': 'AppLovin user acquisition campaigns'
                },
                'UnityUA': {
                    'type': 'expense',
                    'description': 'Unity Ads user acquisition campaigns'
                },
                'MarketingMintegral': {
                    'type': 'expense',
                    'description': 'Mintegral marketing campaigns'
                },
                
                # Tax and fee categories
                'FED': {
                    'type': 'expense',
                    'description': 'Federal Excise Duty and related fees'
                },
                'ProfitTax': {
                    'type': 'expense',
                    'description': 'Corporate profit tax payments'
                },
                'Zakat': {
                    'type': 'expense',
                    'description': 'Zakat payments (religious obligation)'
                },
                
                # Investment and other
                'Investments': {
                    'type': 'expense',
                    'description': 'Investment in assets, stocks, or other ventures'
                },
                'Donation': {
                    'type': 'expense',
                    'description': 'Charitable donations and contributions'
                },
                
                # Transfer categories
                'TransferEntry': {
                    'type': 'transfer',
                    'description': 'Money transfers between accounts'
                },
                'TransferCredit': {
                    'type': 'transfer',
                    'description': 'Transfer credits and adjustments'
                },
            }
            
            # Import categories
            created_count = 0
            skipped_count = 0
            
            for _, row in categories_df.iterrows():
                category_name = row['Category']
                if pd.isna(category_name):
                    continue
                
                # Get category info from intelligence mapping
                cat_info = category_intelligence.get(category_name, {
                    'type': 'expense',  # Default to expense
                    'description': f'Category: {category_name}'
                })
                
                category_type = cat_info['type']
                description = cat_info['description']
                
                # Create for each team
                for team in teams:
                    if not dry_run:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            team=team,
                            category_type=category_type,
                            defaults={
                                'description': description,
                                'is_active': True
                            }
                        )
                        
                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ Created: {category_name} ({category_type}) for {team.name}'
                                )
                            )
                        else:
                            skipped_count += 1
                            self.stdout.write(
                                f'  Exists: {category_name} for {team.name}'
                            )
                    else:
                        self.stdout.write(
                            f'Would create: {category_name} ({category_type}) for {team.name} - {description}'
                        )
            
            # Summary
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('Dry run completed - no changes made to database')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Categories import completed! Created: {created_count}, Skipped: {skipped_count}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing categories: {e}')
            )
