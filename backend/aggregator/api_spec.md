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
- `location_name` (`string | null`) — Sensor display name derived from the CSV metadata

```bash
curl -s http://127.0.0.1:8000/locations
```
```json
{
  "1274947": {
    "latitude": 43.95222,
    "longitude": -78.9125,
    "files": [
      "1274947_no.csv",
      "1274947_no2.csv",
      "1274947_nox.csv",
      "1274947_o3.csv"
    ],
    "location_name": "Oshawa"
  },
  "1274949": {
    "latitude": 43.78043,
    "longitude": -79.467397,
    "files": [
      "1274949_no.csv",
      "1274949_no2.csv",
      "1274949_nox.csv",
      "1274949_o3.csv",
      "1274949_pm25.csv",
      "1274949_so2.csv"
    ],
    "location_name": "North York"
  }
  ...
}
```

**Error Response:** Standard FastAPI error payload (e.g., `500`).

**Notes:** Use the returned IDs to query `/locations/{location_id}`.

### GET /locations/{location_id}
Return the list of pollutant/measurement parameters available for a specific location. The endpoint inspects the CSV filenames listed in `/locations` and surfaces a deduplicated list.

**Path Parameters:**
- `location_id` (string, required) — Must match a key from `/locations`.

**Query Parameters:** none

**Success Response:** `200 OK`
- JSON array of parameter identifiers derived from the sensor's CSV filenames (e.g., `pm25`, `o3`, `temperature`).

```bash
curl -s http://127.0.0.1:8000/locations/1274947
```
```json
[
  "pm1",
  "pm25",
  "relativehumidity",
  "temperature",
  "um003"
]
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
- Parameters preserve the source file naming; apply any user-facing labels in the client.
- Request the raw CSVs (or expose a dedicated endpoint) if you need the full measurement records.

### GET /locations/{location_id}/{parameter}
Return the full measurement records for a single parameter at a location. The payload mirrors the underlying transformed CSV.

**Path Parameters:**
- `location_id` (string, required) — Must match a key from `/locations`.
- `parameter` (string, required) — One of the parameter identifiers returned by `/locations/{location_id}`.

**Query Parameters:** none

**Success Response:** `200 OK`
- JSON array of measurement records for the requested parameter. Fields are derived from the CSV headers.

```bash
curl -s http://127.0.0.1:8000/locations/1274947/pm25 | jq '.[0]'
```
```json
{
  "location_id": 1274947,
  "location_name": "Oshawa",
  "parameter": "pm25",
  "value": 8.6,
  "unit": "ug/m3",
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
- `200 OK` with `{ "error": "Parameter not found" }` when the parameter is absent for that sensor.

**Notes:**
- Measurements with missing values emit `null` so the payload is valid JSON.

### GET /locations/{location_id}/{parameter}/{date}
Return a date-filtered subset of records for a specific parameter. The `date` filter matches the prefix of the `datetimeLocal` field (`YYYY-MM-DD`).

**Path Parameters:**
- `location_id` (string, required)
- `parameter` (string, required)
- `date` (string, required) — Format `YYYY-MM-DD`; compared to `datetimeLocal`.

**Success Response:** `200 OK`
- JSON array filtered down to rows where `datetimeLocal` starts with the supplied date.

```bash
curl -s http://127.0.0.1:8000/locations/1274947/pm25/2025-10-04 | jq length
```
```json
24
```

**Notes:**
- Returns an empty array when no records match the requested date.
- Filtering happens after loading the CSV; add caching if this endpoint becomes hot.

## Local Setup
1. Install dependencies: `pip install -r backend/aggregator/requirements.txt`
2. Start the API server:
   ```bash
   uvicorn backend.aggregator.api:app --reload --host 0.0.0.0 --port 8000
   ```

Ensure the `backend/openaq/transformed` directory contains the latest ETL outputs before starting the service.
