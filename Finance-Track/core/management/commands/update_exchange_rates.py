from django.core.management.base import BaseCommand
from core.models import Currency
from decimal import Decimal


class Command(BaseCommand):
    help = 'Update currency exchange rates'

    def add_arguments(self, parser):
        parser.add_argument('--usd', type=float, help='USD to PKR rate')
        parser.add_argument('--gbp', type=float, help='GBP to PKR rate')
        parser.add_argument('--auto', action='store_true', help='Fetch rates from API (placeholder)')

    def handle(self, *args, **options):
        if options['auto']:
            self.stdout.write('Auto-fetch from API not implemented yet.')
            self.stdout.write('You can integrate with APIs like:')
            self.stdout.write('- https://exchangerate-api.com/')
            self.stdout.write('- https://api.currencylayer.com/')
            self.stdout.write('- https://api.fixer.io/')
            return

        updated = []
        
        if options['usd']:
            usd_currency = Currency.objects.get(code='USD')
            usd_currency.exchange_rate_to_pkr = Decimal(str(options['usd']))
            usd_currency.save()
            updated.append(f"USD: {options['usd']} PKR")
        
        if options['gbp']:
            gbp_currency = Currency.objects.get(code='GBP')
            gbp_currency.exchange_rate_to_pkr = Decimal(str(options['gbp']))
            gbp_currency.save()
            updated.append(f"GBP: {options['gbp']} PKR")
        
        if updated:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated: {", ".join(updated)}')
            )
        else:
            self.stdout.write('No rates updated. Use --usd or --gbp options.')
            
        # Show current rates
        self.stdout.write('\nCurrent Exchange Rates:')
        for currency in Currency.objects.all():
            self.stdout.write(f'{currency.code}: 1 {currency.code} = {currency.exchange_rate_to_pkr} PKR')
