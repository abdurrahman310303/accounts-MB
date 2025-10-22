from django.core.management.base import BaseCommand
from core.models import Category


class Command(BaseCommand):
    help = 'Set up hierarchical category structure: Income, Expense, Transfer with their subcategories'

    def handle(self, *args, **options):
        self.stdout.write("Setting up hierarchical category structure...")
        
        # Clear existing categories
        Category.objects.all().delete()
        
        # Create main categories
        income_main = Category.objects.create(
            name="Income",
            category_type="income",
            description="All types of income and revenue"
        )
        
        expense_main = Category.objects.create(
            name="Expense", 
            category_type="expense",
            description="All types of expenses and costs"
        )
        
        transfer_main = Category.objects.create(
            name="Transfer",
            category_type="transfer", 
            description="Money transfers between accounts"
        )
        
        self.stdout.write(f"✓ Created main categories: Income, Expense, Transfer")
        
        # Income subcategories
        income_subcategories = [
            ("Revenue", "Business revenue and sales income"),
            ("AdMob Income", "Google AdMob advertising revenue"),
            ("Investment Returns", "Returns from investments and assets"),
            ("A/C Receivable", "Accounts receivable - money owed to company"),
            ("Other Income", "Miscellaneous income sources"),
        ]
        
        for name, description in income_subcategories:
            Category.objects.create(
                name=name,
                category_type="income",
                parent=income_main,
                description=description
            )
        
        self.stdout.write(f"✓ Created {len(income_subcategories)} income subcategories")
        
        # Expense subcategories 
        expense_subcategories = [
            # Personal expenses
            ("Saad Personal", "Personal drawings and expenses for Saad"),
            ("Kashif Personal", "Personal drawings and expenses for Kashif"), 
            ("Nasir Personal", "Personal drawings and expenses for Nasir"),
            
            # Business expenses
            ("Office Rent", "Office rental and related costs"),
            ("Equipment", "Equipment purchases and maintenance"),
            ("Company Expense", "General company operational expenses"),
            ("Salaries", "Employee salaries and compensation"),
            ("Marketing", "General marketing and advertising expenses"),
            ("Home Expense", "Home-related expenses (utilities, etc.)"),
            ("Repairing", "Repair and maintenance costs"),
            
            # Marketing & User Acquisition
            ("Google AdWords UA", "Google AdWords user acquisition campaigns"),
            ("TikTok UA", "TikTok user acquisition campaigns"),
            ("AppLovin UA", "AppLovin user acquisition campaigns"),
            ("Unity UA", "Unity Ads user acquisition campaigns"),
            
            # Taxes and Fees
            ("Profit Tax", "Corporate profit tax payments"),
            ("FED", "Federal Excise Duty and related fees"),
            
            # Others
            ("Donation", "Charitable donations and contributions"),
            ("Zakat", "Zakat payments (religious obligation)"),
            ("Investments", "Investment in assets, stocks, or other ventures"),
        ]
        
        for name, description in expense_subcategories:
            Category.objects.create(
                name=name,
                category_type="expense", 
                parent=expense_main,
                description=description
            )
        
        self.stdout.write(f"✓ Created {len(expense_subcategories)} expense subcategories")
        
        # Transfer subcategories
        transfer_subcategories = [
            ("Account Transfer", "Money transfers between accounts"),
            ("Transfer Credit", "Transfer credits and adjustments"),
            ("Currency Exchange", "Currency conversion transfers"),
        ]
        
        for name, description in transfer_subcategories:
            Category.objects.create(
                name=name,
                category_type="transfer",
                parent=transfer_main, 
                description=description
            )
        
        self.stdout.write(f"✓ Created {len(transfer_subcategories)} transfer subcategories")
        
        # Summary
        total_main = Category.objects.filter(parent=None).count()
        total_sub = Category.objects.filter(parent__isnull=False).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCategory setup completed!\n"
                f"Main categories: {total_main}\n"
                f"Subcategories: {total_sub}\n"
                f"Total categories: {total_main + total_sub}"
            )
        )
