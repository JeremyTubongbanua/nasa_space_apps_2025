# Aggregator API Specification

## Overview
The Aggregator service exposes a lightweight REST API backed by pre-processed OpenAQ datasets stored in `backend/openaq/transformed`. All responses are JSON. The service currently runs with FastAPI at `http://localhost:8000` by default.

## Authentication
None. All endpoints are public within the trusted network. Add auth middleware before exposing externally.

## Endpoints

### GET /locations
Retrieve the catalog of OpenAQ locations that have transformed CSV data stored locally.

**Query Parameters:** none

**Success Response:** `200 OK` — JSON object keyed by `location_id`.
- `latitude` (`float`)
- `longitude` (`float`)
- `files` (`string[]`) — CSV filenames in `backend/openaq/transformed/`

```bash
curl -s http://127.0.0.1:8000/locations | jq '."1274947"'
```
```json
{
  "latitude": 43.95222,
  "longitude": -78.9125,
  "files": [
    "1274947_no.csv",
    "1274947_no2.csv",
    "1274947_nox.csv",
    "1274947_o3.csv"
  ]
}
```

**Error Response:** Standard FastAPI error payload (e.g., `500`).

**Notes:** Use the returned IDs to query `/locations/{location_id}`.

### GET /locations/{location_id}
Return pollutant time series for a specific location. The endpoint loads each CSV listed in `/locations` and returns its rows under a key that matches the pollutant/parameter name.

**Path Parameters:**
- `location_id` (string, required) — Must match a key from `/locations`.

**Query Parameters:** none

**Success Response:** `200 OK`
- JSON object with one entry per pollutant (e.g., `pm25`, `o3`, `no2`).
- Each value is an array of measurement records derived directly from the CSV rows. Columns surfaced today:
  - `location_id`, `location_name`, `parameter`
  - `value`, `unit`
  - `datetimeUtc`, `datetimeLocal`, `timezone`
  - `latitude`, `longitude`
  - `country_iso`, `isMobile`, `isMonitor`, `owner_name`, `provider`
- Missing or non-numeric values are serialized as `null` so the payload is JSON compliant.

```bash
curl -s http://127.0.0.1:8000/locations/1274947 | jq '.o3[0]'
```
```json
{
  "location_id": 1274947,
  "location_name": "Oshawa",
  "parameter": "o3",
  "value": 0.042,
  "unit": "ppm",
  "datetimeUtc": "2025-10-04T00:00:00Z",
  "datetimeLocal": "2025-10-03T20:00:00-04:00",
  "timezone": "America/Toronto",
  "latitude": 43.95222,
  "longitude": -78.9125,
  "country_iso": null,
  "isMobile": null,
  "isMonitor": null,
  "owner_name": "Unknown Governmental Organization",
  "provider": "AirNow"
}
```

**Error Responses:**
- `200 OK` with `{ "error": "Location not found" }` when the ID is missing.

```bash
curl -s http://127.0.0.1:8000/locations/does-not-exist
```
```json
{"error":"Location not found"}
```

**Notes:**
- CSVs are read on each request; add caching if latency becomes an issue.
- Fields are returned without unit conversions yet. Consumers must normalize if needed.

## Local Setup
1. Install dependencies: `pip install -r backend/aggregator/requirements.txt`
2. Start the API server:
   ```bash
   uvicorn backend.aggregator.api:app --reload --host 0.0.0.0 --port 8000
   ```

Ensure the `backend/openaq/transformed` directory contains the latest ETL outputs before starting the service.
