import logging
from agri.services.data_gov_client import DataGovClient
from petroleum.models import (
    CrudeOilProduction, RefineryProcessing,
    PetroleumProductProduction, PetroleumImportExportSnapshot,
    PetroleumTrade,
)

logger = logging.getLogger(__name__)

API_CRUDE_PRODUCTION = 'https://api.data.gov.in/resource/7932c3ed-c88d-4e0c-bc39-17e3e3170483'
API_REFINERY_PROCESSING = 'https://api.data.gov.in/resource/8d3b6596-b09e-4077-aebf-425193185a5b'
API_PRODUCT_PRODUCTION = 'https://api.data.gov.in/resource/8b75d7c2-814b-4eb2-9698-c96d69e5f128'
API_IMPORT_EXPORT_SNAPSHOT = 'https://api.data.gov.in/resource/afd0ccfc-cc56-4a4c-a0ab-de187670edfc'
API_PETROLEUM_TRADE = 'https://api.data.gov.in/resource/518e560e-7fa7-4f5b-8aed-3b90323ed965'

MONTH_NAME_TO_NUM = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


class PetroleumSyncService:
    def __init__(self):
        self.client = DataGovClient()

    @staticmethod
    def _safe_float(val):
        try:
            if val is None or str(val).strip() in ('', 'NA', 'na'):
                return None
            return float(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(val):
        try:
            return int(float(val)) if val else None
        except (ValueError, TypeError):
            return None

    def sync_crude_production(self):
        """API 1: ~168 records."""
        result = self.client.fetch_page(API_CRUDE_PRODUCTION, limit=500)
        count = 0
        for record in result['records']:
            month = (record.get('month') or '').strip()
            year = self._safe_int(record.get('year'))
            company = (record.get('company_name') or '').strip()
            if not all([month, year, company]):
                continue
            CrudeOilProduction.objects.update_or_create(
                month=month, year=year, company_name=company,
                defaults={
                    'quantity': self._safe_float(
                        record.get('quantity_000_metric_tonnes_')
                    ),
                },
            )
            count += 1
        logger.info(f"Synced {count} crude oil production records")
        return count

    def sync_refinery_processing(self):
        """API 2: ~1392 records."""
        total_synced = 0
        for batch in self.client.fetch_all(
            API_REFINERY_PROCESSING, batch_size=500, delay=1.0
        ):
            for record in batch:
                month = (record.get('_month_') or '').strip()
                year = self._safe_int(record.get('year'))
                refinery = (record.get('oil_companies_') or '').strip()
                if not all([month, year, refinery]):
                    continue
                RefineryProcessing.objects.update_or_create(
                    month=month, year=year, refinery_name=refinery,
                    defaults={
                        'quantity': self._safe_float(
                            record.get('quantity_000_metric_tonnes_')
                        ),
                    },
                )
                total_synced += 1
        logger.info(f"Synced {total_synced} refinery processing records")
        return total_synced

    def sync_product_production(self):
        """API 3: ~360 records."""
        result = self.client.fetch_page(API_PRODUCT_PRODUCTION, limit=500)
        count = 0
        for record in result['records']:
            month = (record.get('month') or '').strip()
            year = self._safe_int(record.get('year'))
            product = (record.get('products') or '').strip()
            if not all([month, year, product]):
                continue
            PetroleumProductProduction.objects.update_or_create(
                month=month, year=year, product=product,
                defaults={
                    'quantity': self._safe_float(
                        record.get('quantity_000_metric_tonnes_')
                    ),
                },
            )
            count += 1
        logger.info(f"Synced {count} petroleum product production records")
        return count

    def sync_import_export_snapshot(self):
        """API 4: ~28 records (static single-year data)."""
        MONTH_FIELDS = [
            'april', 'may', 'june', 'july', 'august', 'september',
            'october', 'november', 'december', 'january', 'february', 'march',
        ]
        result = self.client.fetch_page(API_IMPORT_EXPORT_SNAPSHOT, limit=50)
        count = 0
        for record in result['records']:
            ie_type = (
                record.get('import_export__quantity_in__000_metric_tonnes_')
                or record.get('import_export')
                or ''
            ).strip()
            product = (record.get('product') or '').strip()
            if not all([ie_type, product]):
                continue
            monthly = {}
            for m in MONTH_FIELDS:
                monthly[m] = self._safe_float(record.get(m))
            PetroleumImportExportSnapshot.objects.update_or_create(
                import_export=ie_type, product=product,
                defaults={
                    'monthly_data': monthly,
                    'total': self._safe_float(record.get('_total')),
                },
            )
            count += 1
        logger.info(f"Synced {count} import/export snapshot records")
        return count

    def sync_petroleum_trade(self):
        """API 5: ~468 records."""
        total_synced = 0
        for batch in self.client.fetch_all(
            API_PETROLEUM_TRADE, batch_size=500, delay=1.0
        ):
            for record in batch:
                month_raw = record.get('Month') or ''
                # Month can be a string name ("April") or a number
                month = self._safe_int(month_raw)
                if month is None:
                    month = MONTH_NAME_TO_NUM.get(str(month_raw).strip().lower())
                year = self._safe_int(record.get('Year'))
                product = (record.get('PRODUCTS') or '').strip()
                trade = (record.get('TRADE') or '').strip()
                if not all([month, year, product, trade]):
                    continue

                date_str = record.get('date_updated')
                date_updated = None
                if date_str and date_str != 'NA':
                    try:
                        from datetime import datetime
                        date_updated = datetime.strptime(
                            date_str.split(' ')[0], '%Y-%m-%d'
                        ).date()
                    except (ValueError, IndexError):
                        pass

                PetroleumTrade.objects.update_or_create(
                    month=month, year=year, product=product, trade_type=trade,
                    defaults={
                        'quantity': self._safe_float(
                            record.get('Quantity (000 Metric Tonnes)')
                        ),
                        'value_inr_crore': self._safe_float(
                            record.get('Value in Rupees (Crore)')
                        ),
                        'value_usd_million': self._safe_float(
                            record.get('Value in Dollars (Million US dollar)')
                        ),
                        'date_updated': date_updated,
                    },
                )
                total_synced += 1
        logger.info(f"Synced {total_synced} petroleum trade records")
        return total_synced
