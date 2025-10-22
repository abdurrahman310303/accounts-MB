from django.core.management.base import BaseCommand
from core.models import Currency


class Command(BaseCommand):
    help = 'Setup initial currencies with exchange rates'

    def handle(self, *args, **options):
        currencies = [
            {
                'code': 'PKR',
                'name': 'Pakistani Rupee',
                'exchange_rate_to_pkr': 1.0000,
            },
            {
                'code': 'USD',
                'name': 'US Dollar',
                'exchange_rate_to_pkr': 280.0000,  # Approximate rate
            },
            {
                'code': 'GBP',
                'name': 'British Pound',
                'exchange_rate_to_pkr': 350.0000,  # Approximate rate
            },
        ]

        for currency_data in currencies:
            currency, created = Currency.objects.get_or_create(
                code=currency_data['code'],
                defaults={
                    'name': currency_data['name'],
                    'exchange_rate_to_pkr': currency_data['exchange_rate_to_pkr'],
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created currency: {currency.code} - {currency.name}')
                )
            else:
                # Update exchange rate if currency already exists
                currency.exchange_rate_to_pkr = currency_data['exchange_rate_to_pkr']
                currency.save()
                self.stdout.write(
                    self.style.WARNING(f'Updated currency: {currency.code} - {currency.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully set up currencies!')
        )
