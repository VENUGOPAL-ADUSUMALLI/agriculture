# Bharat Krishi Setu — Complete API Specification

**Base URL:** `http://localhost:8000/api/v1/`

**Authentication:** Token-based. After login/register, include the token in all subsequent requests:
```
Authorization: Token <your_token_here>
```

**Pagination:** All list endpoints return paginated responses (50 items per page):
```json
{
  "count": 120,
  "next": "http://localhost:8000/api/v1/states/?page=2",
  "previous": null,
  "results": [...]
}
```

**Error Format:**
```json
{
  "error": "Description of what went wrong"
}
```

---

## 1. AUTHENTICATION

---

### 1.1 Register

Create a new user account with optional state/district profile.

```
POST /api/v1/auth/register/
```

**Auth Required:** No

**Request Body:**

| Field         | Type    | Required | Description                                |
|---------------|---------|----------|--------------------------------------------|
| `username`    | string  | Yes      | Unique username (max 150 chars)            |
| `password`    | string  | Yes      | Password (min 8 chars)                     |
| `email`       | string  | No       | Email address                              |
| `first_name`  | string  | No       | First name                                 |
| `last_name`   | string  | No       | Last name                                  |
| `state_id`    | integer | No       | ID of the user's state (from /states/)     |
| `district_id` | integer | No       | ID of the user's district (from /districts/) |
| `designation` | string  | No       | Job title (e.g., "District Agriculture Officer") |

**Example Request:**
```json
{
  "username": "telangana_officer",
  "password": "secure_password_123",
  "email": "officer@telangana.gov.in",
  "first_name": "Ravi",
  "last_name": "Kumar",
  "state_id": 15,
  "district_id": 220,
  "designation": "State Procurement Officer"
}
```

**Success Response:** `201 Created`
```json
{
  "token": "a1b2c3d4e5f6789012345678abcdef90abcdef12",
  "user_id": 1,
  "username": "telangana_officer"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "username": ["Username already exists."]
}
```

---

### 1.2 Login

Authenticate and receive an auth token.

```
POST /api/v1/auth/login/
```

**Auth Required:** No

**Request Body:**

| Field      | Type   | Required | Description |
|------------|--------|----------|-------------|
| `username` | string | Yes      | Username    |
| `password` | string | Yes      | Password    |

**Example Request:**
```json
{
  "username": "telangana_officer",
  "password": "secure_password_123"
}
```

**Success Response:** `200 OK`
```json
{
  "token": "a1b2c3d4e5f6789012345678abcdef90abcdef12",
  "user_id": 1,
  "username": "telangana_officer",
  "profile": {
    "state": 15,
    "state_name": "Telangana",
    "district": 220,
    "district_name": "Hyderabad",
    "designation": "State Procurement Officer",
    "phone": ""
  }
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "error": "Invalid credentials"
}
```

---

### 1.3 Logout

Invalidate the current auth token.

```
POST /api/v1/auth/logout/
```

**Auth Required:** Yes

**Request Body:** None

**Success Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

---

## 2. REFERENCE DATA (Read-Only)

All reference data endpoints are read-only and support pagination, search, and filtering.

---

### 2.1 List States

```
GET /api/v1/states/
```

**Auth Required:** Yes

**Query Parameters:**

| Param    | Type   | Description                        |
|----------|--------|------------------------------------|
| `search` | string | Search by state name (partial match) |
| `page`   | int    | Page number                        |

**Response:** `200 OK`
```json
{
  "count": 20,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Andhra Pradesh",
      "code": null,
      "capital_city": ""
    },
    {
      "id": 2,
      "name": "Arunachal Pradesh",
      "code": null,
      "capital_city": ""
    }
  ]
}
```

---

### 2.2 Get State Detail

```
GET /api/v1/states/{id}/
```

**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Andhra Pradesh",
  "code": null,
  "capital_city": ""
}
```

---

### 2.3 List Districts

```
GET /api/v1/districts/
```

**Auth Required:** Yes

**Query Parameters:**

| Param    | Type    | Description                           |
|----------|---------|---------------------------------------|
| `state`  | integer | Filter by state ID (**most common use**) |
| `search` | string  | Search by district name               |
| `page`   | int     | Page number                           |

**Example:** `GET /api/v1/districts/?state=1`

**Response:** `200 OK`
```json
{
  "count": 23,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 45,
      "name": "Anantapur",
      "state": 1,
      "state_name": "Andhra Pradesh"
    },
    {
      "id": 46,
      "name": "Chittoor",
      "state": 1,
      "state_name": "Andhra Pradesh"
    }
  ]
}
```

---

### 2.4 Get District Detail

```
GET /api/v1/districts/{id}/
```

**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "id": 45,
  "name": "Anantapur",
  "state": 1,
  "state_name": "Andhra Pradesh"
}
```

---

### 2.5 List Crops

```
GET /api/v1/crops/
```

**Auth Required:** Yes

**Query Parameters:**

| Param    | Type   | Description                                 |
|----------|--------|---------------------------------------------|
| `search` | string | Search by crop name or group (partial match) |
| `page`   | int    | Page number                                 |

**Response:** `200 OK`
```json
{
  "count": 73,
  "next": "http://localhost:8000/api/v1/crops/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Arecanut",
      "group": "",
      "typical_season": ""
    },
    {
      "id": 2,
      "name": "Arhar/Tur",
      "group": "",
      "typical_season": ""
    },
    {
      "id": 3,
      "name": "Bajra",
      "group": "",
      "typical_season": ""
    },
    {
      "id": 15,
      "name": "Rice",
      "group": "",
      "typical_season": ""
    }
  ]
}
```

---

### 2.6 Get Crop Detail

```
GET /api/v1/crops/{id}/
```

**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "id": 15,
  "name": "Rice",
  "group": "",
  "typical_season": ""
}
```

---

### 2.7 List Crop Production Data

District-wise, season-wise production statistics (from 1997).

```
GET /api/v1/production/
```

**Auth Required:** Yes

**Query Parameters:**

| Param       | Type    | Description                |
|-------------|---------|----------------------------|
| `crop`      | integer | Filter by crop ID          |
| `state`     | integer | Filter by state ID         |
| `crop_year` | integer | Filter by year (e.g., 2014) |
| `season`    | string  | Filter by season (Kharif, Rabi, Whole Year, etc.) |
| `page`      | int     | Page number                |

**Example:** `GET /api/v1/production/?crop=15&state=1&crop_year=2014`

**Response:** `200 OK`
```json
{
  "count": 23,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 4521,
      "state_name": "Andhra Pradesh",
      "district_name": "Anantapur",
      "crop_name": "Rice",
      "crop_year": 2014,
      "season": "Kharif",
      "area": 52340.0,
      "production": 187560.0
    }
  ]
}
```

**Field Descriptions:**

| Field        | Unit     | Description                   |
|--------------|----------|-------------------------------|
| `area`       | hectares | Cultivated area               |
| `production` | tonnes   | Production quantity            |

---

### 2.8 List Demand & Supply (National)

National-level demand/supply projections from NITI Aayog (15 crop groups).

```
GET /api/v1/demand-supply/
```

**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "crop_group": "Rice",
      "projected_demand_2016_17": 110.0,
      "projected_demand_2020_21": 117.0,
      "projected_supply_2016_17_low": 98.0,
      "projected_supply_2016_17_high": 106.0,
      "actual_production_2006_07": 93.0,
      "actual_production_2011_12": 104.0
    },
    {
      "id": 2,
      "crop_group": "Wheat",
      "projected_demand_2016_17": 89.0,
      "projected_demand_2020_21": 98.0,
      "projected_supply_2016_17_low": 93.0,
      "projected_supply_2016_17_high": 104.0,
      "actual_production_2006_07": 76.0,
      "actual_production_2011_12": 94.0
    }
  ]
}
```

**Field Descriptions:**

| Field                              | Unit           | Description                        |
|------------------------------------|----------------|------------------------------------|
| `projected_demand_2016_17`         | million tonnes | Projected demand for FY 2016-17    |
| `projected_demand_2020_21`         | million tonnes | Projected demand for FY 2020-21    |
| `projected_supply_2016_17_low`     | million tonnes | Projected supply lower bound       |
| `projected_supply_2016_17_high`    | million tonnes | Projected supply upper bound       |
| `actual_production_2006_07`        | million tonnes | Actual production in FY 2006-07    |
| `actual_production_2011_12`        | million tonnes | Actual production in FY 2011-12    |

---

### 2.9 List Crop Prices

MSP-based price data per crop per state.

```
GET /api/v1/prices/
```

**Auth Required:** Yes

**Query Parameters:**

| Param  | Type    | Description          |
|--------|---------|----------------------|
| `crop` | integer | Filter by crop ID    |
| `state`| integer | Filter by state ID   |
| `year` | integer | Filter by year       |
| `page` | int     | Page number          |

**Example:** `GET /api/v1/prices/?crop=15&state=1`

**Response:** `200 OK`
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 234,
      "crop": 15,
      "crop_name": "Rice",
      "state": 1,
      "state_name": "Andhra Pradesh",
      "price_per_tonne": "23145.50",
      "year": 2024,
      "source": "MSP"
    }
  ]
}
```

---

## 3. CORE BUSINESS ENDPOINTS

---

### 3.1 Optimize Procurement (Main Feature)

Submit a procurement request. The system finds all supplier states for the selected crop, calculates cost/distance/delivery/carbon for each, and returns ranked recommendations.

```
POST /api/v1/optimize/
```

**Auth Required:** Yes

**Request Body:**

| Field            | Type    | Required | Description                                      |
|------------------|---------|----------|--------------------------------------------------|
| `crop_id`        | integer | Yes      | ID of the crop to procure (from /crops/)          |
| `state_id`       | integer | Yes      | ID of the buyer's state (from /states/)           |
| `district_id`    | integer | Yes      | ID of the buyer's district (from /districts/)     |
| `quantity_tonnes` | float  | Yes      | Required quantity in tonnes (min: 1)              |

**Example Request:**
```json
{
  "crop_id": 15,
  "state_id": 15,
  "district_id": 220,
  "quantity_tonnes": 500
}
```

**Success Response:** `201 Created`
```json
{
  "id": 1,
  "crop_name": "Rice",
  "state_name": "Telangana",
  "district_name": "Hyderabad",
  "required_quantity_tonnes": 500.0,
  "created_at": "2026-02-11T14:30:00.000000+05:30",
  "results": [
    {
      "id": 1,
      "supplier_state_name": "Andhra Pradesh",
      "available_supply_tonnes": 12500000.0,
      "price_per_tonne": "23145.50",
      "transportation_cost": "312500.00",
      "total_cost": "11885250.00",
      "distance_km": 250.0,
      "estimated_delivery_days": 1.3,
      "carbon_footprint_kg": 7750.0,
      "ranking_category": "best_cost",
      "ranking_score": 0.0
    },
    {
      "id": 2,
      "supplier_state_name": "Chhattisgarh",
      "available_supply_tonnes": 8750000.0,
      "price_per_tonne": "21980.00",
      "transportation_cost": "1125000.00",
      "total_cost": "12115000.00",
      "distance_km": 900.0,
      "estimated_delivery_days": 1.9,
      "carbon_footprint_kg": 27900.0,
      "ranking_category": "",
      "ranking_score": 0.35
    },
    {
      "id": 3,
      "supplier_state_name": "Bihar",
      "available_supply_tonnes": 6500000.0,
      "price_per_tonne": "22400.00",
      "transportation_cost": "1875000.00",
      "total_cost": "13075000.00",
      "distance_km": 1500.0,
      "estimated_delivery_days": 2.6,
      "carbon_footprint_kg": 46500.0,
      "ranking_category": "",
      "ranking_score": 0.72
    }
  ]
}
```

**Response Field Descriptions:**

| Field                    | Type    | Description                                         |
|--------------------------|---------|-----------------------------------------------------|
| `id`                     | int     | Unique query ID (use for /results/ endpoint)        |
| `crop_name`              | string  | Name of the requested crop                          |
| `state_name`             | string  | Buyer's state                                       |
| `district_name`          | string  | Buyer's district                                    |
| `required_quantity_tonnes`| float  | Requested quantity                                  |
| `created_at`             | datetime| Timestamp of the query                              |
| `results`                | array   | Array of ranked procurement options (see below)     |

**Result Object Fields:**

| Field                    | Type    | Unit     | Description                                              |
|--------------------------|---------|----------|----------------------------------------------------------|
| `supplier_state_name`    | string  | —        | Name of the supplier state                               |
| `available_supply_tonnes`| float   | tonnes   | Total production available in that state                 |
| `price_per_tonne`        | decimal | INR      | Crop price per tonne in the supplier state               |
| `transportation_cost`    | decimal | INR      | Transport cost = distance x INR 2.50/km/tonne x quantity|
| `total_cost`             | decimal | INR      | (price x quantity) + transportation_cost                 |
| `distance_km`            | float   | km       | Road distance from supplier to buyer (Google Maps)       |
| `estimated_delivery_days`| float   | days     | (distance/40 kmph + 24h loading) / 24                    |
| `carbon_footprint_kg`    | float   | kg CO2   | distance x quantity x 0.062 kg CO2/tonne-km              |
| `ranking_category`       | string  | —        | `best_cost`, `fastest`, `lowest_carbon`, or empty        |
| `ranking_score`          | float   | 0-1      | Weighted score: 50% cost + 25% delivery + 25% carbon. Lower is better |

**Error Response:** `400 Bad Request`
```json
{
  "error": "Crop matching query does not exist."
}
```

---

### 3.2 Get Query Results (with AI Summary)

Retrieve detailed results for a previous procurement query, including an AI-generated recommendation summary.

```
GET /api/v1/results/{query_id}/
```

**Auth Required:** Yes

**Path Parameters:**

| Param      | Type | Description                              |
|------------|------|------------------------------------------|
| `query_id` | int  | ID of the procurement query (from /optimize/) |

**Response:** `200 OK`
```json
{
  "id": 1,
  "crop_name": "Rice",
  "state_name": "Telangana",
  "district_name": "Hyderabad",
  "required_quantity_tonnes": 500.0,
  "created_at": "2026-02-11T14:30:00.000000+05:30",
  "results": [
    {
      "id": 1,
      "supplier_state_name": "Andhra Pradesh",
      "available_supply_tonnes": 12500000.0,
      "price_per_tonne": "23145.50",
      "transportation_cost": "312500.00",
      "total_cost": "11885250.00",
      "distance_km": 250.0,
      "estimated_delivery_days": 1.3,
      "carbon_footprint_kg": 7750.0,
      "ranking_category": "best_cost",
      "ranking_score": 0.0
    }
  ],
  "ai_summary": "Based on the analysis, procuring Rice from Andhra Pradesh is the optimal choice for Telangana. At a total cost of INR 1,18,85,250 for 500 tonnes, it offers the lowest cost, fastest delivery (1.3 days), and smallest carbon footprint (7,750 kg CO2). The proximity of Andhra Pradesh (250 km) provides significant savings of INR 11,89,750 compared to sourcing from Bihar. For a balanced approach considering all three factors, Andhra Pradesh scores 0.0 on the weighted ranking scale, making it the clear recommendation."
}
```

**Notes:**
- `ai_summary` is generated by OpenAI (GPT-4o-mini) on each request
- If OpenAI is unavailable, `ai_summary` will be `null`
- Only returns queries belonging to the authenticated user

**Error Response:** `404 Not Found`
```json
{
  "error": "Query not found"
}
```

---

### 3.3 Query History

Get the authenticated user's last 20 procurement queries with all their results.

```
GET /api/v1/history/
```

**Auth Required:** Yes

**Response:** `200 OK`
```json
[
  {
    "id": 3,
    "crop_name": "Wheat",
    "state_name": "Maharashtra",
    "district_name": "Pune",
    "required_quantity_tonnes": 1000.0,
    "created_at": "2026-02-11T16:00:00.000000+05:30",
    "results": [...]
  },
  {
    "id": 1,
    "crop_name": "Rice",
    "state_name": "Telangana",
    "district_name": "Hyderabad",
    "required_quantity_tonnes": 500.0,
    "created_at": "2026-02-11T14:30:00.000000+05:30",
    "results": [...]
  }
]
```

---

### 3.4 Crop Availability

See which states produce a specific crop and how much, using the most recent data year.

```
GET /api/v1/crop-availability/?crop={crop_id}
```

**Auth Required:** Yes

**Query Parameters:**

| Param  | Type    | Required | Description    |
|--------|---------|----------|----------------|
| `crop` | integer | Yes      | Crop ID        |

**Example:** `GET /api/v1/crop-availability/?crop=15`

**Response:** `200 OK`
```json
{
  "crop": {
    "id": 15,
    "name": "Rice",
    "group": "",
    "typical_season": ""
  },
  "data_year": 2014,
  "states": [
    {
      "state__id": 1,
      "state__name": "Andhra Pradesh",
      "total_production": 12543210.0,
      "total_area": 3890250.0,
      "district_count": 18
    },
    {
      "state__id": 7,
      "state__name": "Chhattisgarh",
      "total_production": 8750400.0,
      "total_area": 3670100.0,
      "district_count": 16
    }
  ]
}
```

**Field Descriptions:**

| Field              | Unit      | Description                                   |
|--------------------|-----------|-----------------------------------------------|
| `data_year`        | year      | Most recent year with data for this crop       |
| `total_production` | tonnes    | Total production across all districts          |
| `total_area`       | hectares  | Total cultivated area across all districts     |
| `district_count`   | count     | Number of districts producing this crop        |

**Error Response:** `400 Bad Request`
```json
{
  "error": "crop query parameter required"
}
```

---

### 3.5 AI Demand Prediction

Get AI-powered demand/production predictions for a crop, optionally filtered by state.

```
GET /api/v1/predict/{crop_id}/
```

**Auth Required:** Yes

**Path Parameters:**

| Param     | Type | Description |
|-----------|------|-------------|
| `crop_id` | int  | Crop ID     |

**Query Parameters:**

| Param   | Type    | Required | Description                         |
|---------|---------|----------|-------------------------------------|
| `state` | integer | No       | State ID (omit for all-India data)  |

**Example:** `GET /api/v1/predict/15/?state=1`

**Response:** `200 OK`
```json
{
  "crop": {
    "id": 15,
    "name": "Rice",
    "group": "",
    "typical_season": ""
  },
  "state": "Andhra Pradesh",
  "historical_data": [
    { "year": 2000, "production": 11234000.0, "area": 3500000.0 },
    { "year": 2001, "production": 10567000.0, "area": 3450000.0 },
    { "year": 2005, "production": 12100000.0, "area": 3600000.0 },
    { "year": 2010, "production": 13450000.0, "area": 3750000.0 },
    { "year": 2014, "production": 12543210.0, "area": 3890250.0 }
  ],
  "prediction": {
    "prediction_year_1": 13200000,
    "prediction_year_2": 13650000,
    "confidence": "medium",
    "reasoning": "Based on the upward trend from 2000-2014 with slight fluctuations, production is expected to continue growing at approximately 2-3% annually."
  }
}
```

**Notes:**
- If OpenAI is unavailable, `prediction` will contain `{"error": "Prediction unavailable: ..."}`
- Historical data is always returned regardless of OpenAI availability
- Without `state` parameter, returns aggregated all-India data

---

### 3.6 Impact Dashboard

Get cumulative impact metrics for the authenticated user.

```
GET /api/v1/impact/
```

**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "total_queries": 12,
  "total_optimized_cost": 145670000.50,
  "total_carbon_footprint_kg": 234500.0,
  "carbon_saved_kg": 15200.0,
  "recent_queries": [
    {
      "id": 12,
      "crop_name": "Wheat",
      "state_name": "Maharashtra",
      "district_name": "Pune",
      "required_quantity_tonnes": 200.0,
      "created_at": "2026-02-11T16:45:00.000000+05:30",
      "results": [...]
    }
  ]
}
```

**Field Descriptions:**

| Field                       | Type  | Description                                       |
|-----------------------------|-------|---------------------------------------------------|
| `total_queries`             | int   | Total optimization queries made by this user      |
| `total_optimized_cost`      | float | Sum of total_cost from all "best_cost" results    |
| `total_carbon_footprint_kg` | float | Sum of carbon from all results (kg CO2)           |
| `carbon_saved_kg`           | float | Sum of carbon from "lowest_carbon" results        |
| `recent_queries`            | array | Last 10 queries with full results                 |

---

## 4. TYPICAL USER FLOW

```
Step 1: POST /api/v1/auth/register/     → Get auth token
Step 2: GET  /api/v1/states/             → Show state dropdown
Step 3: GET  /api/v1/districts/?state=15 → Show district dropdown (after state selected)
Step 4: GET  /api/v1/crops/              → Show crop dropdown
Step 5: GET  /api/v1/crop-availability/?crop=15  → Show which states have this crop
Step 6: POST /api/v1/optimize/           → Submit procurement request, get ranked results
Step 7: GET  /api/v1/results/1/          → Get detailed results with AI recommendation
Step 8: GET  /api/v1/impact/             → View cumulative savings dashboard
```

---

## 5. FORMULAS USED IN OPTIMIZATION

| Calculation            | Formula                                                    |
|------------------------|------------------------------------------------------------|
| **Transport Cost**     | `distance_km × 2.50 INR/km/tonne × quantity_tonnes`       |
| **Total Cost**         | `(price_per_tonne × quantity) + transport_cost`            |
| **Delivery Time**      | `(distance_km / 40 km/h + 24 hours) / 24` → days          |
| **Carbon Footprint**   | `distance_km × quantity_tonnes × 0.062 kg CO2/tonne-km`   |
| **Ranking Score**      | `0.50 × norm(cost) + 0.25 × norm(delivery) + 0.25 × norm(carbon)` |

Lower ranking score = better overall option.

---

## 6. HTTP STATUS CODES

| Code | Meaning                                                |
|------|--------------------------------------------------------|
| 200  | Success                                                |
| 201  | Created (register, optimize)                           |
| 400  | Bad request (validation errors, missing parameters)    |
| 401  | Unauthorized (invalid/missing token)                   |
| 404  | Not found (invalid ID)                                 |
| 500  | Internal server error                                  |
