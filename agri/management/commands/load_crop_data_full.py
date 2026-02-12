import time
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from agri.models import Crop, CropProduction, District, State


class Command(BaseCommand):
    help = "Load all crop production data from data.gov.in into Django models"

    MAX_RETRIES = 5
    TIMEOUT = 120

    def add_arguments(self, parser):
        parser.add_argument(
            "--api-key",
            type=str,
            default=None,
            help="Data.gov.in API key (defaults to DATA_GOV_API_KEY from .env)",
        )
        parser.add_argument(
            "--base-url",
            type=str,
            default=getattr(
                settings,
                "CROP_PRODUCTION_API_URL",
                "https://api.data.gov.in/resource/35be999b-0208-4354-b557-f6ca9a5355de",
            ),
            help="Crop production resource URL",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=getattr(settings, "DATA_GOV_BATCH_SIZE", 246091),
            help="Records per API request",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=getattr(settings, "DATA_GOV_REQUEST_DELAY", 0.5),
            help="Delay between requests in seconds",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="Optional crop year filter",
        )

    def handle(self, *args, **options):
        api_key = options["api_key"] or getattr(settings, "DATA_GOV_API_KEY", None)
        if not api_key:
            raise CommandError("Missing API key. Set DATA_GOV_API_KEY or pass --api-key.")

        base_url = options["base_url"]
        limit = options["limit"]
        delay = options["delay"]
        crop_year = options["year"]

        if limit <= 0:
            raise CommandError("--limit must be a positive integer.")
        if delay < 0:
            raise CommandError("--delay cannot be negative.")

        session = requests.Session()

        state_cache = {}
        district_cache = {}
        crop_cache = {}

        total = None
        offset = 0
        processed = 0
        staged_for_insert = 0

        self.stdout.write(self.style.NOTICE("Starting crop data load..."))
        self.stdout.write(f"Endpoint: {base_url}")
        self.stdout.write(f"Batch size: {limit}, Delay: {delay}s")
        if crop_year:
            self.stdout.write(f"Year filter: {crop_year}")

        while True:
            params = {
                "api-key": api_key,
                "format": "json",
                "offset": offset,
                "limit": limit,
            }
            if crop_year:
                params["filters[crop_year]"] = crop_year

            response_json = self._fetch_with_retry(session, base_url, params)

            if total is None:
                total = int(response_json.get("total", 0) or 0)
                self.stdout.write(f"Total records reported by API: {total}")

            records = response_json.get("records", [])
            if not records:
                break

            production_objects = []

            for record in records:
                state_name = (record.get("state_name") or "").strip().title()
                district_name = (record.get("district_name") or "").strip().title()
                crop_name = (record.get("crop") or "").strip().title()
                season = (record.get("season") or "").strip()

                if not state_name or not district_name or not crop_name or not season:
                    continue

                year_value = self._safe_int(record.get("crop_year"))
                if year_value is None:
                    continue

                state = self._get_or_create_state(state_name, state_cache)
                district = self._get_or_create_district(
                    district_name, state, district_cache
                )
                crop = self._get_or_create_crop(crop_name, crop_cache)

                production_objects.append(
                    CropProduction(
                        state=state,
                        district=district,
                        crop=crop,
                        crop_year=year_value,
                        season=season,
                        area=self._safe_float(record.get("area_")),
                        production=self._safe_float(record.get("production_")),
                    )
                )

            if production_objects:
                with transaction.atomic():
                    CropProduction.objects.bulk_create(
                        production_objects,
                        ignore_conflicts=True,
                        batch_size=500,
                    )
                staged_for_insert += len(production_objects)

            batch_count = len(records)
            processed += batch_count
            offset += batch_count

            if total:
                self.stdout.write(f"Fetched {min(processed, total)} / {total}")
            else:
                self.stdout.write(f"Fetched {processed}")

            if total and offset >= total:
                break

            if delay:
                time.sleep(delay)

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed. Processed {processed} records, staged {staged_for_insert} for insert."
            )
        )

    def _fetch_with_retry(self, session, base_url, params):
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = session.get(base_url, params=params, timeout=self.TIMEOUT)
                if response.status_code >= 500:
                    raise requests.exceptions.HTTPError(
                        f"Server error: {response.status_code}", response=response
                    )
                response.raise_for_status()
                return response.json()
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
            ) as exc:
                if attempt == self.MAX_RETRIES:
                    raise CommandError(f"API request failed after {self.MAX_RETRIES} attempts: {exc}")
                wait = 2 ** attempt
                self.stdout.write(
                    self.style.WARNING(
                        f"Request failed (attempt {attempt}/{self.MAX_RETRIES}): {exc}. Retrying in {wait}s..."
                    )
                )
                time.sleep(wait)

    @staticmethod
    def _safe_float(value):
        if value is None:
            return None
        str_val = str(value).strip()
        if str_val in ("", "NA", "na", "N/A", "n/a"):
            return None
        try:
            return float(str_val)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value):
        if value is None:
            return None
        str_val = str(value).strip()
        if str_val in ("", "NA", "na", "N/A", "n/a"):
            return None
        try:
            return int(float(str_val))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_or_create_state(name, cache):
        if name not in cache:
            state, _ = State.objects.get_or_create(name=name)
            cache[name] = state
        return cache[name]

    @staticmethod
    def _get_or_create_district(name, state, cache):
        key = (name, state.id)
        if key not in cache:
            district, _ = District.objects.get_or_create(name=name, state=state)
            cache[key] = district
        return cache[key]

    @staticmethod
    def _get_or_create_crop(name, cache):
        if name not in cache:
            crop, _ = Crop.objects.get_or_create(name=name)
            cache[name] = crop
        return cache[name]
