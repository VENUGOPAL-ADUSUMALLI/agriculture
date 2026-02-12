import sys
from django.core.management.base import BaseCommand
from agri.models import RailwayFreightRate

# Distance slabs: (min_km, max_km)
SLABS = [
    (1, 100), (101, 125), (126, 150), (151, 175), (176, 200),
    (201, 225), (226, 250), (251, 275), (276, 300), (301, 325),
    (326, 350), (351, 375), (376, 400), (401, 425), (426, 450),
    (451, 475), (476, 500), (501, 550), (551, 600), (601, 650),
    (651, 700), (701, 750), (751, 800), (801, 850), (851, 900),
    (901, 950), (951, 1000), (1001, 1100), (1101, 1200), (1201, 1300),
    (1301, 1400), (1401, 1500), (1501, 1625), (1626, 1750), (1751, 1875),
    (1876, 2000), (2001, 2125), (2126, 2250), (2251, 2375), (2376, 2500),
    (2501, 2625), (2626, 2750), (2751, 2875), (2876, 3000), (3001, 3125),
    (3126, 3250), (3251, 3375), (3376, 3500),
]

# Class 130A - Train Load - Food Grains, Flours & Pulses
RATES_130A = [
    147.4, 184.3, 224.8, 251.9, 281.7, 309.3, 338.9, 368.6, 397.8, 425.5,
    454.2, 483.0, 512.2, 541.7, 571.0, 599.7, 629.7, 689.1, 748.0, 806.4,
    864.5, 923.1, 980.6, 1038.2, 1095.5, 1152.7, 1209.9, 1325.5, 1441.3, 1556.6,
    1671.3, 1785.9, 1897.2, 2043.2, 2101.1, 2241.1, 2263.7, 2396.8, 2418.5, 2545.8,
    2585.8, 2708.9, 2747.3, 2866.8, 2903.7, 3019.9, 3056.0, 3169.1,
]

# Class 130B - Wagon Load - Food Grains, Flours & Pulses
RATES_130B = [
    162.2, 202.8, 247.3, 277.1, 309.9, 340.3, 372.8, 405.5, 437.6, 468.1,
    499.7, 531.3, 563.5, 595.9, 628.1, 659.7, 692.7, 758.1, 822.8, 887.1,
    951.0, 1015.5, 1078.7, 1142.1, 1205.1, 1268.0, 1330.9, 1458.1, 1585.5, 1712.3,
    1838.5, 1964.5, 2087.0, 2247.6, 2311.3, 2465.3, 2490.1, 2636.5, 2660.4, 2800.4,
    2844.4, 2979.8, 3022.1, 3153.5, 3194.1, 3321.9, 3361.6, 3486.1,
]

# Class LR3 - Train Load - Sugar, Salt, Spices, Oils (Turmeric)
RATES_LR3 = [
    86.3, 107.8, 125.2, 140.6, 157.0, 172.4, 189.0, 205.5, 221.9, 237.1,
    253.2, 269.2, 285.7, 302.2, 318.4, 334.5, 351.2, 384.2, 417.1, 449.6,
    482.1, 514.7, 546.7, 579.0, 611.0, 642.8, 674.8, 739.2, 803.9, 868.1,
    932.1, 996.0, 1058.2, 1139.6, 1171.8, 1249.9, 1262.4, 1336.6, 1348.9, 1419.8,
    1441.9, 1510.6, 1532.2, 1598.8, 1619.4, 1684.1, 1704.3, 1767.5,
]

# Class LR3W - Wagon Load - Sugar, Salt, Spices, Oils (Turmeric)
RATES_LR3W = [
    95.0, 118.6, 137.8, 154.7, 172.7, 189.7, 207.9, 226.1, 244.1, 260.9,
    278.6, 296.2, 314.3, 332.5, 350.3, 368.0, 386.4, 422.7, 458.9, 494.6,
    530.4, 566.2, 601.4, 636.9, 672.1, 707.1, 742.3, 813.2, 884.3, 955.0,
    1025.4, 1095.6, 1164.1, 1253.6, 1289.0, 1374.9, 1388.7, 1470.3, 1483.8, 1561.8,
    1586.1, 1661.7, 1685.5, 1758.7, 1781.4, 1852.6, 1874.8, 1944.3,
]

RATE_CLASSES = {
    '130A': RATES_130A,
    '130B': RATES_130B,
    'LR3': RATES_LR3,
    'LR3W': RATES_LR3W,
}


class Command(BaseCommand):
    help = 'Seed Indian Railways freight rate slabs for agricultural commodities'

    def handle(self, *args, **options):
        sys.stdout.reconfigure(encoding='utf-8')

        records = []
        for rate_class, rates in RATE_CLASSES.items():
            for i, (min_km, max_km) in enumerate(SLABS):
                records.append(RailwayFreightRate(
                    rate_class=rate_class,
                    min_distance_km=min_km,
                    max_distance_km=max_km,
                    rate_per_tonne=rates[i],
                ))

        RailwayFreightRate.objects.all().delete()
        created = RailwayFreightRate.objects.bulk_create(records)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(created)} railway freight rate slabs '
            f'(4 classes x {len(SLABS)} distance slabs)'
        ))

        # Summary
        for rc in RATE_CLASSES:
            count = RailwayFreightRate.objects.filter(rate_class=rc).count()
            self.stdout.write(f'  {rc}: {count} slabs')
