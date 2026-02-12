# Petroleum Sector — Complete API Specification

**Base URL:** `http://localhost:8000/api/v1/petroleum/`

**Authentication:** Token-based. Include the token from `/api/v1/auth/login/` in all requests:
```
Authorization: Token <your_token_here>
```

**Pagination:** All list (ViewSet) endpoints return paginated responses (50 items per page):
```json
{
  "count": 168,
  "next": "http://localhost:8000/api/v1/petroleum/crude-production/?page=2",
  "previous": null,
  "results": [...]
}
```

**Units:** All quantities are in **000 metric tonnes** unless stated otherwise. Values are in **INR Crore** or **USD Million**.

**Data Source:** All data is sourced from [data.gov.in](https://data.gov.in) — Ministry of Petroleum & Natural Gas, Government of India.

---

## Table of Contents

1. [Data Browsing Endpoints](#1-data-browsing-endpoints)
   - 1.1 [Crude Oil Production](#11-crude-oil-production)
   - 1.2 [Refinery Processing](#12-refinery-processing)
   - 1.3 [Petroleum Product Production](#13-petroleum-product-production)
   - 1.4 [Import/Export Snapshot](#14-importexport-snapshot)
   - 1.5 [Petroleum Trade](#15-petroleum-trade)
2. [Analytics Endpoints](#2-analytics-endpoints)
   - 2.1 [Crude Oil Production Forecast](#21-crude-oil-production-forecast)
   - 2.2 [Refinery Utilization Analysis](#22-refinery-utilization-analysis)
   - 2.3 [Product Demand-Supply Gap](#23-product-demand-supply-gap)
   - 2.4 [Import Cost Analysis](#24-import-cost-analysis)
   - 2.5 [Trade Balance Dashboard](#25-trade-balance-dashboard)
   - 2.6 [AI Market Intelligence](#26-ai-market-intelligence)
3. [Utility Endpoints](#3-utility-endpoints)
   - 3.1 [Filter Options](#31-filter-options)

---

## 1. DATA BROWSING ENDPOINTS

All data endpoints are read-only ViewSets supporting `list` and `retrieve` actions. No authentication is required for browsing.

---

### 1.1 Crude Oil Production

Monthly indigenous crude oil production data by company (ONGC, OIL, Private/JV).

#### List All Records

```
GET /api/v1/petroleum/crude-production/
```

**Auth Required:** No

**Query Parameters:**

| Parameter      | Type    | Required | Description                                      |
|----------------|---------|----------|--------------------------------------------------|
| `year`         | integer | No       | Filter by year (e.g., `2023`)                    |
| `company_name` | string  | No       | Filter by company name (exact match)             |
| `search`       | string  | No       | Search in `company_name`                         |
| `ordering`     | string  | No       | Sort by `year` or `quantity` (prefix `-` for desc) |
| `page`         | integer | No       | Page number for pagination                       |

**Example Request:**
```
GET /api/v1/petroleum/crude-production/?company_name=ONGC&year=2023&ordering=-quantity
```

**Success Response:** `200 OK`
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "month": "January",
      "year": 2023,
      "company_name": "ONGC",
      "quantity": 1520.3
    },
    {
      "id": 2,
      "month": "February",
      "year": 2023,
      "company_name": "ONGC",
      "quantity": 1480.7
    }
  ]
}
```

**Field Descriptions:**

| Field          | Type    | Description                               |
|----------------|---------|-------------------------------------------|
| `id`           | integer | Unique record ID                          |
| `month`        | string  | Month name (e.g., "January")              |
| `year`         | integer | Calendar year                             |
| `company_name` | string  | Oil company (ONGC, OIL, Private/JV, etc.) |
| `quantity`     | float   | Production in 000 metric tonnes           |

#### Retrieve Single Record

```
GET /api/v1/petroleum/crude-production/{id}/
```

**Success Response:** `200 OK`
```json
{
  "id": 1,
  "month": "January",
  "year": 2023,
  "company_name": "ONGC",
  "quantity": 1520.3
}
```

---

### 1.2 Refinery Processing

Monthly crude oil processed by each refinery in India (23+ refineries).

#### List All Records

```
GET /api/v1/petroleum/refinery-processing/
```

**Auth Required:** No

**Query Parameters:**

| Parameter       | Type    | Required | Description                                      |
|-----------------|---------|----------|--------------------------------------------------|
| `year`          | integer | No       | Filter by year                                   |
| `refinery_name` | string  | No       | Filter by refinery name (exact match)            |
| `search`        | string  | No       | Search in `refinery_name`                        |
| `ordering`      | string  | No       | Sort by `year` or `quantity` (prefix `-` for desc) |
| `page`          | integer | No       | Page number for pagination                       |

**Example Request:**
```
GET /api/v1/petroleum/refinery-processing/?refinery_name=Jamnagar Refinery&year=2022
```

**Success Response:** `200 OK`
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 45,
      "month": "April",
      "year": 2022,
      "refinery_name": "Jamnagar Refinery",
      "quantity": 3200.5
    },
    {
      "id": 46,
      "month": "May",
      "year": 2022,
      "refinery_name": "Jamnagar Refinery",
      "quantity": 3180.2
    }
  ]
}
```

**Field Descriptions:**

| Field           | Type    | Description                                 |
|-----------------|---------|---------------------------------------------|
| `id`            | integer | Unique record ID                            |
| `month`         | string  | Month name (e.g., "April")                  |
| `year`          | integer | Calendar year                               |
| `refinery_name` | string  | Refinery name (e.g., "Jamnagar Refinery")   |
| `quantity`      | float   | Crude oil processed in 000 metric tonnes    |

---

### 1.3 Petroleum Product Production

Monthly production of petroleum products (LPG, Petrol/MS, Diesel/HSD, ATF, Naphtha, etc.) by refineries and fractionators.

#### List All Records

```
GET /api/v1/petroleum/product-production/
```

**Auth Required:** No

**Query Parameters:**

| Parameter  | Type    | Required | Description                                      |
|------------|---------|----------|--------------------------------------------------|
| `year`     | integer | No       | Filter by year                                   |
| `product`  | string  | No       | Filter by product name (exact match)             |
| `search`   | string  | No       | Search in `product`                              |
| `ordering` | string  | No       | Sort by `year` or `quantity` (prefix `-` for desc) |
| `page`     | integer | No       | Page number for pagination                       |

**Example Request:**
```
GET /api/v1/petroleum/product-production/?product=LPG&ordering=-year
```

**Success Response:** `200 OK`
```json
{
  "count": 36,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 120,
      "month": "March",
      "year": 2025,
      "product": "LPG",
      "quantity": 1250.8
    },
    {
      "id": 108,
      "month": "February",
      "year": 2025,
      "product": "LPG",
      "quantity": 1190.3
    }
  ]
}
```

**Field Descriptions:**

| Field     | Type    | Description                                    |
|-----------|---------|------------------------------------------------|
| `id`      | integer | Unique record ID                               |
| `month`   | string  | Month name                                     |
| `year`    | integer | Calendar year                                  |
| `product` | string  | Product name (LPG, Petrol/MS, HSD, ATF, etc.) |
| `quantity` | float  | Production in 000 metric tonnes                |

---

### 1.4 Import/Export Snapshot

Month-wise import and export volumes for petroleum products for FY 2022-23. This is a static single-year dataset with monthly breakdowns stored as JSON.

#### List All Records

```
GET /api/v1/petroleum/import-export-snapshot/
```

**Auth Required:** No

**Query Parameters:**

| Parameter       | Type   | Required | Description                                |
|-----------------|--------|----------|--------------------------------------------|
| `import_export` | string | No       | Filter by type: `"Import"` or `"Export"`   |
| `product`       | string | No       | Filter by product name (exact match)       |
| `search`        | string | No       | Search in `product`                        |
| `page`          | integer| No       | Page number for pagination                 |

**Example Request:**
```
GET /api/v1/petroleum/import-export-snapshot/?import_export=Import
```

**Success Response:** `200 OK`
```json
{
  "count": 14,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "import_export": "Import",
      "product": "LPG",
      "monthly_data": {
        "april": 720.5,
        "may": 680.3,
        "june": 710.8,
        "july": 750.2,
        "august": 690.1,
        "september": 700.4,
        "october": 730.6,
        "november": 740.9,
        "december": 760.3,
        "january": 780.1,
        "february": 720.5,
        "march": 770.0
      },
      "total": 8753.7
    }
  ]
}
```

**Field Descriptions:**

| Field           | Type    | Description                                                   |
|-----------------|---------|---------------------------------------------------------------|
| `id`            | integer | Unique record ID                                              |
| `import_export` | string  | `"Import"` or `"Export"`                                      |
| `product`       | string  | Product name                                                  |
| `monthly_data`  | object  | Month-wise volumes (April–March, FY 2022-23) in 000 MT       |
| `total`         | float   | Annual total in 000 metric tonnes                             |

---

### 1.5 Petroleum Trade

Multi-year monthly import/export data with quantity and value breakdowns by product.

#### List All Records

```
GET /api/v1/petroleum/trade/
```

**Auth Required:** No

**Query Parameters:**

| Parameter    | Type    | Required | Description                                        |
|--------------|---------|----------|----------------------------------------------------|
| `year`       | integer | No       | Filter by year                                     |
| `product`    | string  | No       | Filter by product name (exact match)               |
| `trade_type` | string  | No       | Filter by `"Import"` or `"Export"`                 |
| `search`     | string  | No       | Search in `product`                                |
| `ordering`   | string  | No       | Sort by `year`, `month`, `quantity`, or `value_inr_crore` |
| `page`       | integer | No       | Page number for pagination                         |

**Example Request:**
```
GET /api/v1/petroleum/trade/?product=Crude Oil&trade_type=Import&year=2025&ordering=-value_inr_crore
```

**Success Response:** `200 OK`
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 301,
      "month": 4,
      "year": 2025,
      "product": "Crude Oil",
      "trade_type": "Import",
      "quantity": 19850.5,
      "value_inr_crore": 125000.0,
      "value_usd_million": 15200.0,
      "date_updated": "2025-06-15"
    },
    {
      "id": 302,
      "month": 5,
      "year": 2025,
      "product": "Crude Oil",
      "trade_type": "Import",
      "quantity": 20100.8,
      "value_inr_crore": 128500.0,
      "value_usd_million": 15600.0,
      "date_updated": "2025-06-15"
    }
  ]
}
```

**Field Descriptions:**

| Field              | Type    | Description                                    |
|--------------------|---------|------------------------------------------------|
| `id`               | integer | Unique record ID                               |
| `month`            | integer | Month as number (1 = January, 12 = December)  |
| `year`             | integer | Calendar year                                  |
| `product`          | string  | Product name (Crude Oil, LPG, Petrol/MS, etc.)|
| `trade_type`       | string  | `"Import"` or `"Export"`                       |
| `quantity`         | float   | Quantity in 000 metric tonnes                  |
| `value_inr_crore`  | float   | Trade value in Indian Rupees (Crore)           |
| `value_usd_million`| float   | Trade value in US Dollars (Million)            |
| `date_updated`     | string  | Date when the record was last updated (ISO)    |

---

## 2. ANALYTICS ENDPOINTS

All analytics endpoints require authentication (`IsAuthenticated`). These provide aggregated analysis, AI-powered forecasts, and strategic intelligence.

---

### 2.1 Crude Oil Production Forecast

**Problem Statement:** India's domestic crude oil production has been declining. This endpoint forecasts future output by company and assesses import requirement implications using AI (GPT-4o-mini).

```
GET /api/v1/petroleum/forecast/crude/
```

**Auth Required:** Yes

**Query Parameters:**

| Parameter | Type   | Required | Description                                          |
|-----------|--------|----------|------------------------------------------------------|
| `company` | string | No       | Company name to filter (e.g., `"ONGC"`). Omit for all. |

**Example Request:**
```
GET /api/v1/petroleum/forecast/crude/?company=ONGC
Authorization: Token a1b2c3d4e5f6...
```

**Success Response:** `200 OK`
```json
{
  "company": "ONGC",
  "historical_data": [
    {
      "year": 2022,
      "company_name": "ONGC",
      "total_quantity": 17520.6
    },
    {
      "year": 2023,
      "company_name": "ONGC",
      "total_quantity": 17105.4
    },
    {
      "year": 2024,
      "company_name": "ONGC",
      "total_quantity": 16780.2
    }
  ],
  "forecast": {
    "forecast": [
      { "year": 2025, "predicted_quantity": 16440.5 },
      { "year": 2026, "predicted_quantity": 16100.8 },
      { "year": 2027, "predicted_quantity": 15760.3 }
    ],
    "trend": "declining",
    "confidence": 0.72,
    "import_implication": "With ONGC production declining at ~2% annually, India will need to increase crude oil imports by approximately 340-400 thousand metric tonnes each year to maintain current refinery throughput levels.",
    "analysis": "ONGC's production shows a consistent downward trend driven by maturing fields in Bombay High and onshore Gujarat. New discoveries in KG Basin and deepwater blocks have not offset the decline. Recommend accelerating enhanced oil recovery (EOR) programs."
  }
}
```

**Field Descriptions:**

| Field                | Type    | Description                                           |
|----------------------|---------|-------------------------------------------------------|
| `company`            | string  | Filtered company name, or `"All"` if not specified    |
| `historical_data`    | array   | Yearly aggregated production by company               |
| `historical_data[].year` | integer | Calendar year                                     |
| `historical_data[].company_name` | string | Company name                             |
| `historical_data[].total_quantity` | float | Total production for that year (000 MT)       |
| `forecast`           | object  | AI-generated forecast (or deterministic fallback)     |
| `forecast.forecast`  | array   | 3-year predicted production                           |
| `forecast.trend`     | string  | `"increasing"`, `"stable"`, or `"declining"`          |
| `forecast.confidence`| float   | Confidence score (0.0 to 1.0)                         |
| `forecast.import_implication` | string | Impact assessment on import requirements      |
| `forecast.analysis`  | string  | Detailed analysis narrative                           |

**Fallback Behavior:** If the AI service is unavailable, a deterministic fallback applies a 2% annual decline rate with `confidence: 0.35`.

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 2.2 Refinery Utilization Analysis

**Problem Statement:** Analyze refinery-wise processing trends, seasonal patterns, and utilization levels across India's 23+ refineries to identify capacity bottlenecks and seasonal demand patterns.

```
GET /api/v1/petroleum/analysis/refinery/
```

**Auth Required:** Yes

**Query Parameters:**

| Parameter  | Type    | Required | Description                                            |
|------------|---------|----------|--------------------------------------------------------|
| `refinery` | string  | No       | Refinery name to filter. Omit for all refineries.      |
| `year`     | integer | No       | Filter by specific year                                |

**Example Request:**
```
GET /api/v1/petroleum/analysis/refinery/?refinery=Jamnagar Refinery&year=2023
Authorization: Token a1b2c3d4e5f6...
```

**Success Response:** `200 OK`
```json
{
  "refinery": "Jamnagar Refinery",
  "year_filter": 2023,
  "yearly_trends": [
    {
      "year": 2023,
      "refinery_name": "Jamnagar Refinery",
      "total_processed": 38400.6
    }
  ],
  "seasonal_pattern": [
    { "month": "April", "avg_quantity": 3150.2 },
    { "month": "May", "avg_quantity": 3280.5 },
    { "month": "June", "avg_quantity": 3050.8 },
    { "month": "July", "avg_quantity": 2980.3 },
    { "month": "August", "avg_quantity": 2850.6 },
    { "month": "September", "avg_quantity": 3100.4 },
    { "month": "October", "avg_quantity": 3350.7 },
    { "month": "November", "avg_quantity": 3400.1 },
    { "month": "December", "avg_quantity": 3380.9 },
    { "month": "January", "avg_quantity": 3250.5 },
    { "month": "February", "avg_quantity": 3080.2 },
    { "month": "March", "avg_quantity": 3420.3 }
  ]
}
```

**Field Descriptions:**

| Field                         | Type    | Description                                    |
|-------------------------------|---------|------------------------------------------------|
| `refinery`                    | string  | Filtered refinery name, or `"All"`             |
| `year_filter`                 | integer | Year filter applied, or `null`                 |
| `yearly_trends`               | array   | Yearly aggregated processing data              |
| `yearly_trends[].year`        | integer | Calendar year                                  |
| `yearly_trends[].refinery_name` | string | Refinery name                                |
| `yearly_trends[].total_processed` | float | Total crude processed that year (000 MT)     |
| `seasonal_pattern`            | array   | Monthly average processing (across all years)  |
| `seasonal_pattern[].month`    | string  | Month name                                     |
| `seasonal_pattern[].avg_quantity` | float | Average monthly processing (000 MT)          |

---

### 2.3 Product Demand-Supply Gap

**Problem Statement:** Compare domestic production vs imports/exports to identify self-sufficiency gaps. India imports LPG heavily but exports diesel — this endpoint reveals those imbalances per product.

```
GET /api/v1/petroleum/analysis/demand-supply-gap/
```

**Auth Required:** Yes

**Query Parameters:**

| Parameter | Type    | Required | Description                                        |
|-----------|---------|----------|----------------------------------------------------|
| `product` | string  | No       | Product name filter (case-insensitive contains)    |
| `year`    | integer | No       | Filter by specific year                            |

**Example Request:**
```
GET /api/v1/petroleum/analysis/demand-supply-gap/?product=LPG&year=2025
Authorization: Token a1b2c3d4e5f6...
```

**Success Response:** `200 OK`
```json
{
  "product_filter": "LPG",
  "year_filter": 2025,
  "production": [
    {
      "product": "LPG",
      "year": 2025,
      "domestic_production": 14200.5
    }
  ],
  "imports": [
    {
      "product": "LPG",
      "year": 2025,
      "import_quantity": 8500.3,
      "import_value_inr": 28000.0
    }
  ],
  "exports": [
    {
      "product": "LPG",
      "year": 2025,
      "export_quantity": 120.5,
      "export_value_inr": 450.0
    }
  ]
}
```

**Field Descriptions:**

| Field                          | Type    | Description                                     |
|--------------------------------|---------|-------------------------------------------------|
| `product_filter`               | string  | Applied product filter, or `"All"`              |
| `year_filter`                  | integer | Applied year filter, or `null`                  |
| `production`                   | array   | Domestic production aggregated by product/year  |
| `production[].product`         | string  | Product name                                    |
| `production[].year`            | integer | Calendar year                                   |
| `production[].domestic_production` | float | Total domestic production (000 MT)            |
| `imports`                      | array   | Import data aggregated by product/year          |
| `imports[].import_quantity`    | float   | Total import quantity (000 MT)                  |
| `imports[].import_value_inr`   | float   | Total import value (INR Crore)                  |
| `exports`                      | array   | Export data aggregated by product/year          |
| `exports[].export_quantity`    | float   | Total export quantity (000 MT)                  |
| `exports[].export_value_inr`   | float   | Total export value (INR Crore)                  |

**Usage Notes:**
- Compare `domestic_production` + `import_quantity` - `export_quantity` to calculate total consumption.
- Products where `import_quantity >> export_quantity` indicate import dependency (e.g., LPG, Crude Oil).
- Products where `export_quantity >> import_quantity` indicate surplus (e.g., Diesel/HSD).

---

### 2.4 Import Cost Analysis

**Problem Statement:** Track and forecast India's petroleum import bill by product. India's crude oil import bill is one of its largest foreign exchange expenditures. This endpoint provides historical import cost data and AI-powered forecasts.

```
GET /api/v1/petroleum/analysis/import-costs/
```

**Auth Required:** Yes

**Query Parameters:**

| Parameter | Type    | Required | Description                          |
|-----------|---------|----------|--------------------------------------|
| `year`    | integer | No       | Filter import data by specific year  |

**Example Request:**
```
GET /api/v1/petroleum/analysis/import-costs/?year=2025
Authorization: Token a1b2c3d4e5f6...
```

**Success Response:** `200 OK`
```json
{
  "year_filter": 2025,
  "import_data": [
    {
      "year": 2025,
      "product": "Crude Oil",
      "total_quantity": 235000.5,
      "total_value_inr": 1200000.0,
      "total_value_usd": 145000.0
    },
    {
      "year": 2025,
      "product": "LPG",
      "total_quantity": 8500.3,
      "total_value_inr": 28000.0,
      "total_value_usd": 3400.0
    }
  ],
  "ai_forecast": {
    "forecast": [
      {
        "year": 2026,
        "estimated_bill_inr_crore": 1320000.0,
        "estimated_bill_usd_million": 159500.0
      },
      {
        "year": 2027,
        "estimated_bill_inr_crore": 1400000.0,
        "estimated_bill_usd_million": 168000.0
      }
    ],
    "key_drivers": [
      "Rising domestic petroleum demand driven by economic growth",
      "Declining domestic crude production increasing import dependency",
      "Global oil price volatility and OPEC+ production decisions",
      "INR/USD exchange rate fluctuations"
    ],
    "risk_factors": [
      "Geopolitical tensions in Middle East disrupting supply",
      "Sudden oil price spikes above $100/barrel",
      "Faster-than-expected transition to EVs reducing demand"
    ],
    "analysis": "India's petroleum import bill is projected to rise 8-10% annually, driven primarily by crude oil imports which constitute over 85% of total petroleum imports. With domestic production declining at ~2% per year and demand growing at ~4%, the import dependency ratio will continue to widen."
  }
}
```

**Field Descriptions:**

| Field                        | Type    | Description                                      |
|------------------------------|---------|--------------------------------------------------|
| `year_filter`                | integer | Applied year filter, or `null`                   |
| `import_data`                | array   | Historical import data by product and year       |
| `import_data[].year`         | integer | Calendar year                                    |
| `import_data[].product`      | string  | Product name                                     |
| `import_data[].total_quantity`    | float  | Total import quantity (000 MT)               |
| `import_data[].total_value_inr`  | float  | Total import value (INR Crore)               |
| `import_data[].total_value_usd`  | float  | Total import value (USD Million)             |
| `ai_forecast`                | object  | AI-generated 2-year import cost forecast         |
| `ai_forecast.forecast`       | array   | Predicted import bills                           |
| `ai_forecast.key_drivers`    | array   | Factors driving import costs                     |
| `ai_forecast.risk_factors`   | array   | Risk factors to watch                            |
| `ai_forecast.analysis`       | string  | Detailed analysis narrative                      |

**Fallback Behavior:** If the AI service is unavailable:
```json
{
  "ai_forecast": {
    "error": "AI forecast unavailable",
    "confidence": 0.0
  }
}
```

---

### 2.5 Trade Balance Dashboard

**Problem Statement:** Determine per-product net importer/exporter status. Shows which products India imports heavily (Crude Oil, LPG) vs exports (Diesel/HSD, Petcoke) with quantity and value breakdowns.

```
GET /api/v1/petroleum/dashboard/trade-balance/
```

**Auth Required:** Yes

**Query Parameters:**

| Parameter | Type    | Required | Description                                |
|-----------|---------|----------|--------------------------------------------|
| `year`    | integer | No       | Filter by year. Omit for all-time totals.  |

**Example Request:**
```
GET /api/v1/petroleum/dashboard/trade-balance/?year=2025
Authorization: Token a1b2c3d4e5f6...
```

**Success Response:** `200 OK`
```json
{
  "year_filter": 2025,
  "products": [
    {
      "product": "Crude Oil",
      "import_quantity": 235000.5,
      "export_quantity": 0.0,
      "net_quantity": -235000.5,
      "status": "net_importer",
      "import_value_inr_crore": 1200000.0,
      "export_value_inr_crore": 0.0
    },
    {
      "product": "Diesel/HSD",
      "import_quantity": 2500.0,
      "export_quantity": 35000.8,
      "net_quantity": 32500.8,
      "status": "net_exporter",
      "import_value_inr_crore": 12000.0,
      "export_value_inr_crore": 165000.0
    },
    {
      "product": "LPG",
      "import_quantity": 8500.3,
      "export_quantity": 120.5,
      "net_quantity": -8379.8,
      "status": "net_importer",
      "import_value_inr_crore": 28000.0,
      "export_value_inr_crore": 450.0
    }
  ]
}
```

**Field Descriptions:**

| Field                      | Type    | Description                                             |
|----------------------------|---------|---------------------------------------------------------|
| `year_filter`              | integer | Applied year filter, or `null`                          |
| `products`                 | array   | Trade balance per product                               |
| `products[].product`       | string  | Product name                                            |
| `products[].import_quantity` | float | Total import quantity (000 MT)                          |
| `products[].export_quantity` | float | Total export quantity (000 MT)                          |
| `products[].net_quantity`  | float   | `export_quantity - import_quantity` (negative = importer)|
| `products[].status`        | string  | `"net_importer"` or `"net_exporter"`                    |
| `products[].import_value_inr_crore` | float | Total import value (INR Crore)                 |
| `products[].export_value_inr_crore` | float | Total export value (INR Crore)                 |

**Usage Notes:**
- `net_quantity` is positive for net exporters, negative for net importers.
- Products are sorted alphabetically.
- Use `status` field for quick UI badges/tags (red for importer, green for exporter).

---

### 2.6 AI Market Intelligence

**Problem Statement:** Generate a comprehensive AI-powered strategic briefing combining all petroleum data sources. Provides actionable insights for Indian policymakers and industry analysts.

```
GET /api/v1/petroleum/intelligence/
```

**Auth Required:** Yes

**Query Parameters:** None

**Example Request:**
```
GET /api/v1/petroleum/intelligence/
Authorization: Token a1b2c3d4e5f6...
```

**Success Response:** `200 OK`
```json
{
  "headline": "India's Petroleum Sector: Rising Import Dependency Amid Declining Domestic Production",
  "key_findings": [
    {
      "title": "Domestic Crude Production Declining",
      "detail": "India's crude oil production has fallen by 3.2% over the past 3 years, with ONGC's aging Bombay High fields contributing to the steepest decline. This widens the import dependency gap."
    },
    {
      "title": "Refinery Capacity Utilization Above 100%",
      "detail": "Indian refineries are operating at above-nameplate capacity, with Jamnagar and Paradip leading throughput. This indicates strong domestic demand and export-oriented refining strategy."
    },
    {
      "title": "LPG Import Dependency Critical",
      "detail": "India imports over 60% of its LPG requirements, making it the world's largest LPG importer. Domestic LPG production covers only ~40% of consumption driven by Ujjwala Yojana expansion."
    },
    {
      "title": "Diesel Export Surplus Generates Forex",
      "detail": "India is a net exporter of Diesel/HSD, with exports exceeding imports by 32,500 TMT. This partially offsets the massive crude oil import bill."
    },
    {
      "title": "Import Bill Concentration Risk",
      "detail": "Crude oil alone accounts for 85%+ of India's total petroleum import bill. Any $10/barrel price increase adds approximately INR 40,000 Crore to the annual import bill."
    }
  ],
  "strategic_recommendations": [
    "Accelerate Enhanced Oil Recovery (EOR) programs in ONGC's mature fields to slow production decline",
    "Diversify crude oil sourcing beyond Middle East to include Guyana, Brazil, and US shale",
    "Fast-track strategic petroleum reserves (SPR) expansion from current 5.3 MMT to 12 MMT",
    "Incentivize domestic LPG production capacity through refinery upgrades and new fractionators",
    "Continue diesel export strategy as forex earner while monitoring domestic supply adequacy"
  ],
  "risk_assessment": "India's petroleum sector faces a dual challenge of declining domestic production and growing demand. The import dependency ratio for crude oil exceeds 85% and is projected to reach 90% by 2030. Geopolitical risks in the Middle East, OPEC+ production decisions, and exchange rate volatility pose significant threats to energy security and current account balance."
}
```

**Field Descriptions:**

| Field                          | Type    | Description                                          |
|--------------------------------|---------|------------------------------------------------------|
| `headline`                     | string  | One-line strategic headline                          |
| `key_findings`                 | array   | 4-6 key analytical findings                          |
| `key_findings[].title`         | string  | Finding title                                        |
| `key_findings[].detail`        | string  | Detailed explanation                                 |
| `strategic_recommendations`    | array   | Actionable policy/strategy recommendations           |
| `risk_assessment`              | string  | Overall risk assessment narrative                    |

**Fallback Behavior:** If the AI service is unavailable:
```json
{
  "headline": "Market Intelligence Unavailable",
  "key_findings": [
    {
      "title": "Service Error",
      "detail": "AI analysis could not be generated. Please try again later."
    }
  ],
  "strategic_recommendations": [],
  "risk_assessment": "Unable to assess at this time."
}
```

---

## 3. UTILITY ENDPOINTS

---

### 3.1 Filter Options

Returns all available distinct values for building filter dropdowns in the UI.

```
GET /api/v1/petroleum/filters/
```

**Auth Required:** Yes

**Query Parameters:** None

**Example Request:**
```
GET /api/v1/petroleum/filters/
Authorization: Token a1b2c3d4e5f6...
```

**Success Response:** `200 OK`
```json
{
  "companies": [
    "OIL",
    "ONGC",
    "Pvt./JV companies"
  ],
  "refineries": [
    "Barauni Refinery",
    "Bina Refinery",
    "CPCL (Manali) Refinery",
    "Digboi Refinery",
    "Gujarat Refinery",
    "Guwahati Refinery",
    "Haldia Refinery",
    "Jamnagar Refinery",
    "Kochi Refinery",
    "Mathura Refinery",
    "Mumbai Refinery",
    "Numaligarh Refinery",
    "Panipat Refinery",
    "Paradip Refinery",
    "Tatipaka Refinery",
    "Vizag Refinery"
  ],
  "production_products": [
    "ATF",
    "Bitumen",
    "Diesel/HSD",
    "Furnace Oil",
    "LPG",
    "Lube Oils",
    "Naphtha",
    "Others",
    "Petroleum Coke",
    "Petrol/MS"
  ],
  "trade_products": [
    "Crude Oil",
    "Diesel/HSD",
    "LPG",
    "Naphtha",
    "Others",
    "Petrol/MS"
  ],
  "years": {
    "crude_production": [2020, 2021, 2022, 2023, 2024],
    "refinery_processing": [2017, 2018, 2019, 2020, 2021, 2022, 2023],
    "product_production": [2022, 2023, 2024, 2025],
    "trade": [2024, 2025, 2026]
  }
}
```

**Field Descriptions:**

| Field                      | Type         | Description                                             |
|----------------------------|--------------|---------------------------------------------------------|
| `companies`                | string[]     | Distinct company names from crude oil production data   |
| `refineries`               | string[]     | Distinct refinery names from refinery processing data   |
| `production_products`      | string[]     | Distinct product names from product production data     |
| `trade_products`           | string[]     | Distinct product names from trade data                  |
| `years`                    | object       | Available years per dataset                             |
| `years.crude_production`   | integer[]    | Years in crude oil production dataset                   |
| `years.refinery_processing`| integer[]    | Years in refinery processing dataset                    |
| `years.product_production` | integer[]    | Years in product production dataset                     |
| `years.trade`              | integer[]    | Years in trade dataset                                  |

**Usage Notes:**
- Call this endpoint once on app load and cache the result.
- Use `companies` for the crude oil production forecast company dropdown.
- Use `refineries` for the refinery utilization analysis refinery dropdown.
- Use `production_products` for demand-supply gap product dropdown.
- Use `trade_products` for trade balance product dropdown.
- Use `years.*` for year dropdowns in each respective section.

---

## Data Sync

Data is synced from data.gov.in using the management command:

```bash
# Sync all 5 datasets
python manage.py sync_petroleum_data

# Sync individual datasets
python manage.py sync_petroleum_data --crude-only      # API 1: Crude Oil Production (~168 records)
python manage.py sync_petroleum_data --refinery-only   # API 2: Refinery Processing (~1392 records)
python manage.py sync_petroleum_data --products-only   # API 3: Product Production (~360 records)
python manage.py sync_petroleum_data --snapshot-only   # API 4: Import/Export Snapshot (~28 records)
python manage.py sync_petroleum_data --trade-only      # API 5: Petroleum Trade (~468 records)
```

**data.gov.in API Endpoints:**

| Dataset                    | API URL                                                        |
|----------------------------|----------------------------------------------------------------|
| Crude Oil Production       | `https://api.data.gov.in/resource/7932c3ed-c88d-4e0c-bc39-17e3e3170483` |
| Refinery Processing        | `https://api.data.gov.in/resource/8d3b6596-b09e-4077-aebf-425193185a5b` |
| Product Production         | `https://api.data.gov.in/resource/8b75d7c2-814b-4eb2-9698-c96d69e5f128` |
| Import/Export Snapshot      | `https://api.data.gov.in/resource/afd0ccfc-cc56-4a4c-a0ab-de187670edfc` |
| Petroleum Trade            | `https://api.data.gov.in/resource/518e560e-7fa7-4f5b-8aed-3b90323ed965` |
