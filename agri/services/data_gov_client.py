import time
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class DataGovClient:
    BASE_TIMEOUT = 120
    MAX_RETRIES = 5

    def __init__(self):
        self.api_key = settings.DATA_GOV_API_KEY
        self.session = requests.Session()

    def fetch_page(self, resource_url, limit=1000, offset=0, filters=None):
        params = {
            'api-key': self.api_key,
            'format': 'json',
            'limit': limit,
            'offset': offset,
        }
        if filters:
            for key, value in filters.items():
                params[f'filters[{key}]'] = value

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(
                    resource_url, params=params, timeout=self.BASE_TIMEOUT
                )
                if response.status_code >= 500:
                    raise requests.exceptions.HTTPError(
                        f"{response.status_code} Server Error", response=response)
                response.raise_for_status()
                data = response.json()
                return {
                    'total': data.get('total', 0),
                    'count': data.get('count', 0),
                    'records': data.get('records', []),
                }
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError) as e:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed: {e}. "
                    f"Retrying in {wait}s...")
                if attempt == self.MAX_RETRIES - 1:
                    raise
                time.sleep(wait)

    def fetch_all(self, resource_url, filters=None, batch_size=1000, delay=0.5):
        offset = 0
        total = None

        while True:
            result = self.fetch_page(
                resource_url, limit=batch_size, offset=offset, filters=filters
            )

            if total is None:
                total = result['total']
                logger.info(f"Total records to fetch: {total}")

            records = result['records']
            if not records:
                break

            yield records

            offset += batch_size
            if offset >= total:
                break

            time.sleep(delay)
            logger.info(f"Fetched {min(offset, total)}/{total} records")

    def fetch_demand_supply(self):
        url = 'https://api.data.gov.in/resource/27ac86aa-0352-4c13-8711-23d4720d82ea'
        result = self.fetch_page(url, limit=20)
        return result['records']

    def fetch_crop_production(self, filters=None):
        url = 'https://api.data.gov.in/resource/35be999b-0208-4354-b557-f6ca9a5355de'
        yield from self.fetch_all(url, filters=filters, batch_size=500, delay=1.0)
