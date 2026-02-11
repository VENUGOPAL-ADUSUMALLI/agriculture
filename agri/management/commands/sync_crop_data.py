from django.core.management.base import BaseCommand
from agri.services.data_sync import DataSyncService


class Command(BaseCommand):
    help = 'Sync crop production data from data.gov.in APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year', type=int, help='Sync only a specific crop year')
        parser.add_argument(
            '--demand-only', action='store_true',
            help='Only sync demand/supply data (15 records)')
        parser.add_argument(
            '--production-only', action='store_true',
            help='Only sync production data (246K records)')

    def handle(self, *args, **options):
        service = DataSyncService()

        if not options['production_only']:
            self.stdout.write('Syncing demand/supply data...')
            count = service.sync_demand_supply()
            self.stdout.write(self.style.SUCCESS(
                f'Synced {count} demand/supply records'))

        if not options['demand_only']:
            self.stdout.write(
                'Syncing crop production data (this may take several minutes)...')
            count = service.sync_crop_production(
                crop_year_filter=options.get('year'))
            self.stdout.write(self.style.SUCCESS(
                f'Synced {count} crop production records'))
