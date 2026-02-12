from django.core.management.base import BaseCommand
from petroleum.services.petroleum_sync import PetroleumSyncService


class Command(BaseCommand):
    help = 'Sync petroleum data from data.gov.in APIs (5 datasets)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crude-only', action='store_true',
            help='Only sync crude oil production (API 1)')
        parser.add_argument(
            '--refinery-only', action='store_true',
            help='Only sync refinery processing (API 2)')
        parser.add_argument(
            '--products-only', action='store_true',
            help='Only sync petroleum product production (API 3)')
        parser.add_argument(
            '--snapshot-only', action='store_true',
            help='Only sync import/export snapshot (API 4)')
        parser.add_argument(
            '--trade-only', action='store_true',
            help='Only sync petroleum trade data (API 5)')

    def handle(self, *args, **options):
        service = PetroleumSyncService()

        specific = any([
            options['crude_only'], options['refinery_only'],
            options['products_only'], options['snapshot_only'],
            options['trade_only'],
        ])

        if not specific or options['crude_only']:
            self.stdout.write('Syncing crude oil production data...')
            count = service.sync_crude_production()
            self.stdout.write(self.style.SUCCESS(
                f'Synced {count} crude oil production records'))

        if not specific or options['refinery_only']:
            self.stdout.write('Syncing refinery processing data...')
            count = service.sync_refinery_processing()
            self.stdout.write(self.style.SUCCESS(
                f'Synced {count} refinery processing records'))

        if not specific or options['products_only']:
            self.stdout.write('Syncing petroleum product production data...')
            count = service.sync_product_production()
            self.stdout.write(self.style.SUCCESS(
                f'Synced {count} petroleum product production records'))

        if not specific or options['snapshot_only']:
            self.stdout.write('Syncing import/export snapshot data...')
            count = service.sync_import_export_snapshot()
            self.stdout.write(self.style.SUCCESS(
                f'Synced {count} import/export snapshot records'))

        if not specific or options['trade_only']:
            self.stdout.write('Syncing petroleum trade data...')
            count = service.sync_petroleum_trade()
            self.stdout.write(self.style.SUCCESS(
                f'Synced {count} petroleum trade records'))

        self.stdout.write(self.style.SUCCESS('Petroleum data sync complete!'))
