import logging
from django.db import transaction
from agri.models import State, District, Crop, CropProduction, DemandSupply
from agri.services.data_gov_client import DataGovClient

logger = logging.getLogger(__name__)


class DataSyncService:

    def __init__(self):
        self.client = DataGovClient()
        self._state_cache = {}
        self._district_cache = {}
        self._crop_cache = {}

    def _get_or_create_state(self, state_name):
        name = state_name.strip().title()
        if name not in self._state_cache:
            state, _ = State.objects.get_or_create(name=name)
            self._state_cache[name] = state
        return self._state_cache[name]

    def _get_or_create_district(self, district_name, state):
        key = (district_name.strip().title(), state.id)
        if key not in self._district_cache:
            district, _ = District.objects.get_or_create(
                name=district_name.strip().title(),
                state=state,
            )
            self._district_cache[key] = district
        return self._district_cache[key]

    def _get_or_create_crop(self, crop_name):
        name = crop_name.strip().title()
        if name not in self._crop_cache:
            crop, _ = Crop.objects.get_or_create(name=name)
            self._crop_cache[name] = crop
        return self._crop_cache[name]

    def sync_demand_supply(self):
        records = self.client.fetch_demand_supply()
        count = 0

        for record in records:
            crop_group = record.get('crop_group_of_crops', '')
            supply_str = str(record.get('projected_supply__by_financial_year_2016_17', ''))

            supply_low, supply_high = None, None
            if supply_str and supply_str != 'NA':
                for sep in ['-', '\u2013', '\u2014']:
                    if sep in supply_str:
                        parts = supply_str.split(sep)
                        try:
                            supply_low = float(parts[0].strip())
                            supply_high = float(parts[1].strip())
                        except (ValueError, IndexError):
                            pass
                        break

            def safe_float(val):
                try:
                    return float(val) if val and str(val) != 'NA' else None
                except (ValueError, TypeError):
                    return None

            DemandSupply.objects.update_or_create(
                crop_group=crop_group,
                defaults={
                    'projected_demand_2016_17': safe_float(
                        record.get('projected_demand__by_financial_year_2016_17')),
                    'projected_demand_2020_21': safe_float(
                        record.get('projected_demand__by_financial_year_2020_21')),
                    'projected_supply_2016_17_low': supply_low,
                    'projected_supply_2016_17_high': supply_high,
                    'actual_production_2006_07': safe_float(
                        record.get('actual_production__for_financial_year_2006_07')),
                    'actual_production_2011_12': safe_float(
                        record.get('actual_production__for_financial_year_2011_12')),
                },
            )
            count += 1

        logger.info(f"Synced {count} demand/supply records")
        return count

    def sync_crop_production(self, crop_year_filter=None):
        filters = {}
        if crop_year_filter:
            filters['crop_year'] = crop_year_filter

        total_synced = 0

        for batch in self.client.fetch_crop_production(filters=filters):
            production_objects = []

            for record in batch:
                try:
                    state = self._get_or_create_state(record.get('state_name', ''))
                    district = self._get_or_create_district(
                        record.get('district_name', ''), state
                    )
                    crop = self._get_or_create_crop(record.get('crop', ''))

                    crop_year = int(float(record.get('crop_year', 0)))

                    area_val = record.get('area_')
                    area = None
                    if area_val is not None and str(area_val).strip() not in ('', 'NA', 'na'):
                        try:
                            area = float(area_val)
                        except (ValueError, TypeError):
                            area = None

                    prod_val = record.get('production_')
                    production = None
                    if prod_val is not None and str(prod_val).strip() not in ('', 'NA', 'na'):
                        try:
                            production = float(prod_val)
                        except (ValueError, TypeError):
                            production = None

                    production_objects.append(CropProduction(
                        state=state,
                        district=district,
                        crop=crop,
                        crop_year=crop_year,
                        season=record.get('season', ''),
                        area=area,
                        production=production,
                    ))
                except Exception as e:
                    logger.warning(f"Skipping record: {e}")
                    continue

            if production_objects:
                CropProduction.objects.bulk_create(
                    production_objects,
                    ignore_conflicts=True,
                    batch_size=500,
                )
                total_synced += len(production_objects)
                logger.info(f"Synced batch: {total_synced} total records")

        return total_synced
