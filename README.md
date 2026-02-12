# Bharat Krishi Setu Backend

Django + Django REST Framework backend for:
- Agricultural procurement optimization and crop intelligence
- Petroleum production/trade analytics

This repository contains two apps:
- `agri`: crop production, demand/supply, pricing, procurement optimization
- `petroleum`: crude/refinery/product/trade datasets and analytics APIs

## Tech Stack
- Python 3.10+
- Django 5.2.x
- Django REST Framework
- SQLite (default)
- External APIs: data.gov.in, Google Maps, OpenAI

## Project Structure
```text
agri_backend/                     # Django project config
agri/                             # Agriculture domain
  management/commands/            # Crop sync + seed commands
  services/                       # Data sync, optimization, cost, AI, maps
petroleum/                        # Petroleum domain
  management/commands/            # Petroleum sync command
  services/                       # Petroleum sync + analytics
API_SPEC.md                       # Agriculture API documentation
PETROLEUM_API_SPEC.md             # Petroleum API documentation
```

## Setup
1. Create and activate virtual environment.
2. Install dependencies.
3. Configure `.env`.
4. Run migrations.
5. Start the server.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Server:
- `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Environment Variables
Create `.env` in project root:

```env
DJANGO_SECRET_KEY=change-me
DEBUG=True

DATA_GOV_API_KEY=your_data_gov_key
DEMAND_SUPPLY_API_URL=https://api.data.gov.in/resource/27ac86aa-0352-4c13-8711-23d4720d82ea
CROP_PRODUCTION_API_URL=https://api.data.gov.in/resource/35be999b-0208-4354-b557-f6ca9a5355de
DATA_GOV_BATCH_SIZE=1000
DATA_GOV_REQUEST_DELAY=0.5

GOOGLE_MAPS_API_KEY=your_google_maps_key
OPENAI_API_KEY=your_openai_key
```

Notes:
- `DATA_GOV_API_KEY` is required for sync commands.
- `GOOGLE_MAPS_API_KEY` is used for distance/cost calculations.
- `OPENAI_API_KEY` is used for AI summaries/intelligence endpoints.

## Database Initialization
Run:

```bash
python manage.py migrate
```

Optional (for Django DB cache backend table):
```bash
python manage.py createcachetable cache_table
```

## Data Loading Commands

### Agriculture
- Sync demand + crop production:
```bash
python manage.py sync_crop_data
```

- Sync only production:
```bash
python manage.py sync_crop_data --production-only
```

- Sync only demand/supply:
```bash
python manage.py sync_crop_data --demand-only
```

- Sync a specific crop year:
```bash
python manage.py sync_crop_data --year 2022
```

- Full standalone loader (single command file implementation):
```bash
python manage.py load_crop_data_full
```

- Full loader with options:
```bash
python manage.py load_crop_data_full --year 2022 --limit 1000 --delay 0.5
```

- Seed crop prices:
```bash
python manage.py seed_price_data --year 2024
```

- Seed railway freight slabs:
```bash
python manage.py seed_railway_rates
```

### Petroleum
- Sync all 5 petroleum datasets:
```bash
python manage.py sync_petroleum_data
```

- Sync specific datasets:
```bash
python manage.py sync_petroleum_data --crude-only
python manage.py sync_petroleum_data --refinery-only
python manage.py sync_petroleum_data --products-only
python manage.py sync_petroleum_data --snapshot-only
python manage.py sync_petroleum_data --trade-only
```

## API Base Paths
- Agriculture APIs: `/api/v1/`
- Petroleum APIs: `/api/v1/petroleum/`

## Authentication
Token authentication is enabled.

Public endpoints:
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`

Authenticated:
- Most business and analytics endpoints
- `POST /api/v1/auth/logout/`

Use token header:
```http
Authorization: Token <your_token>
```

## Main Agriculture Endpoints
- `GET /api/v1/states/`
- `GET /api/v1/districts/?state=<state_id>`
- `GET /api/v1/crops/`
- `GET /api/v1/production/`
- `GET /api/v1/demand-supply/`
- `GET /api/v1/demand-supply/insights/?crop=Rice`
- `GET /api/v1/prices/`
- `POST /api/v1/optimize/`
- `GET /api/v1/history/`
- `GET /api/v1/results/<query_uuid>/`
- `GET /api/v1/dashboard/`

## Main Petroleum Endpoints
- `GET /api/v1/petroleum/crude-production/`
- `GET /api/v1/petroleum/refinery-processing/`
- `GET /api/v1/petroleum/product-production/`
- `GET /api/v1/petroleum/import-export-snapshot/`
- `GET /api/v1/petroleum/trade/`
- `GET /api/v1/petroleum/forecast/crude/`
- `GET /api/v1/petroleum/analysis/refinery/`
- `GET /api/v1/petroleum/analysis/demand-supply-gap/`
- `GET /api/v1/petroleum/analysis/import-costs/`
- `GET /api/v1/petroleum/dashboard/trade-balance/`
- `GET /api/v1/petroleum/intelligence/`
- `GET /api/v1/petroleum/filters/`

## API Documentation Files
- Agriculture: `API_SPEC.md`
- Petroleum: `PETROLEUM_API_SPEC.md`

## Quick Verification
After sync, check record counts:

```bash
python manage.py shell -c "from agri.models import CropProduction; print(CropProduction.objects.count())"
python manage.py shell -c "from petroleum.models import PetroleumTrade; print(PetroleumTrade.objects.count())"
```

## Troubleshooting
- `ModuleNotFoundError: No module named 'django'`
  - Activate virtualenv and install requirements.
- Empty sync results
  - Verify `DATA_GOV_API_KEY` in `.env`.
- 401 on APIs
  - Login and pass `Authorization: Token <token>`.

