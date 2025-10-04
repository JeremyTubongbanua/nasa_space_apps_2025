# OpenAQ Flask Proxy

This project wraps the OpenAQ v3 API in a lightweight Flask service and provides sample endpoints matching the official OpenAQ cURL examples. The proxy passes requests through to OpenAQ when possible and serves built-in sample payloads when running offline.

## Prerequisites

- Python 3.9 or later
- [`uv`](https://github.com/astral-sh/uv) for dependency and script management
- An OpenAQ API key (optional, recommended for live upstream data)

## Installation

Clone the repository, then install dependencies:

```bash
uv pip install -r requirements.txt
```

## Running the API

From the project root:

```bash
export OPENAQ_KEY="your_api_key"  # optional; omit to use fallback data
uv run main.py
```

The server listens on `http://127.0.0.1:8000` by default. Set `HOST` or `PORT` environment variables to override the bind address or port.

## Key Endpoints

All responses follow the OpenAQ schema. When the upstream API is unreachable, the proxy returns curated sample data so the endpoints always respond successfully.

- `GET /health` — Basic service status check.
- `GET /locations` — Accepts OpenAQ query parameters such as `parameters_id`, `coordinates`, `radius`, `bbox`, `limit`, and `page`.
- `GET /sensors/<sensor_id>/measurements` — Returns recent measurements for a sensor.
- `GET /sensors/<sensor_id>/days` — Provides daily aggregates for a sensor.
- `GET /sensors/<sensor_id>/days/yearly` — Provides yearly aggregates derived from daily data.
- `GET /parameters/<parameter_id>/latest` — Returns the latest values for a pollutant parameter (e.g., PM₂.₅ when `parameter_id=2`).

Refer to [`curl.md`](./curl.md) for ready-to-use cURL examples that hit each endpoint.

## Sample cURL Commands

These commands assume the API is running locally on `http://127.0.0.1:8000`. Remove the `| jq` portion if you do not have `jq` installed. Each command succeeds even without network access because the proxy serves fallback payloads when OpenAQ cannot be reached.

```bash
# Filter locations by parameter (PM2.5)
curl -s "http://127.0.0.1:8000/locations?parameters_id=2&limit=5" | jq

# Find locations near coordinates (longitude,latitude) within a radius
coords="136.90610,35.14942"
curl -s "http://127.0.0.1:8000/locations?coordinates=${coords}&radius=12000&limit=5" | jq

# Find locations inside a bounding box (xmin,ymin,xmax,ymax)
bbox="-118.668153,33.703935,-118.155358,34.337306"
curl -s "http://127.0.0.1:8000/locations?bbox=${bbox}&limit=5" | jq

# Fetch original measurements for sensor 3917
curl -s "http://127.0.0.1:8000/sensors/3917/measurements?limit=5" | jq

# Fetch daily averages for sensor 3917
curl -s "http://127.0.0.1:8000/sensors/3917/days?limit=7" | jq

# Fetch yearly averages for sensor 3917
curl -s "http://127.0.0.1:8000/sensors/3917/days/yearly?limit=3" | jq

# Get the latest PM2.5 values (parameter 2)
curl -s "http://127.0.0.1:8000/parameters/2/latest?limit=3" | jq
```
