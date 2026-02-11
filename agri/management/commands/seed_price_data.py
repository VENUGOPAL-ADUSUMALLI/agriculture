import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from agri.models import State, Crop, CropPrice


# MSP rates (INR per tonne) based on Government of India data
MSP_PRICES = {
    'Rice': 22030,
    'Wheat': 22750,
    'Maize': 21200,
    'Jowar': 31000,
    'Bajra': 25500,
    'Ragi': 38460,
    'Barley': 18800,
    'Sugarcane': 3150,
    'Cotton(Lint)': 67200,
    'Cotton': 67200,
    'Jute': 52000,
    'Groundnut': 60150,
    'Soyabean': 44920,
    'Sunflower': 63800,
    'Sesamum': 82000,
    'Rapeseed &Mustard': 56500,
    'Rapeseed': 56500,
    'Safflower': 57680,
    'Niger Seed': 76710,
    'Arhar/Tur': 70000,
    'Moong(Green Gram)': 83480,
    'Urad': 69670,
    'Lentil': 63250,
    'Gram': 55250,
    'Masoor': 63250,
    'Coconut': 30900,
    'Arecanut': 70000,
    'Banana': 12000,
    'Onion': 15000,
    'Potato': 10000,
    'Tomato': 18000,
    'Turmeric': 80000,
    'Black Pepper': 350000,
    'Dry Chillies': 120000,
    'Ginger': 40000,
    'Garlic': 50000,
    'Tapioca': 8000,
    'Sweet Potato': 12000,
    'Tobacco': 55000,
    'Coffee': 200000,
    'Tea': 150000,
    'Rubber': 140000,
    'Cashewnut': 120000,
    'Coriander': 70000,
    'Horse-Gram': 35000,
    'Ragi': 38460,
    'Other Kharif Pulses': 65000,
    'Other Rabi Pulses': 65000,
    'Other Cereals & Millets': 25000,
    'Other Oilseeds': 55000,
}

# Default price for crops not in MSP list
DEFAULT_PRICE = 25000


class Command(BaseCommand):
    help = 'Seed crop price data based on MSP rates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year', type=int, default=2024,
            help='Year for price data (default: 2024)')

    def handle(self, *args, **options):
        year = options['year']
        states = State.objects.all()
        crops = Crop.objects.all()

        if not states.exists():
            self.stdout.write(self.style.ERROR(
                'No states found. Run sync_crop_data first.'))
            return

        if not crops.exists():
            self.stdout.write(self.style.ERROR(
                'No crops found. Run sync_crop_data first.'))
            return

        created_count = 0

        for crop in crops:
            base_price = MSP_PRICES.get(crop.name, DEFAULT_PRICE)

            for state in states:
                # Add state-level variation (+/- 15%)
                variation = random.uniform(0.85, 1.15)
                price = round(base_price * variation, 2)

                _, created = CropPrice.objects.update_or_create(
                    crop=crop,
                    state=state,
                    year=year,
                    defaults={
                        'price_per_tonne': Decimal(str(price)),
                        'source': 'MSP',
                    },
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {created_count} price records for {crops.count()} crops '
            f'across {states.count()} states (year {year})'))
