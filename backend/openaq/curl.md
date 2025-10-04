# Sample Curl Commands for the Flask OpenAQ Proxy

Run the API locally with:

```bash
export OPENAQ_KEY="your_api_key_here"  # optional, fallback data is used if omitted or offline
uv run main.py
```

Once the server is listening on `http://127.0.0.1:8000`, try the commands below. They mirror the examples from the official OpenAQ docs but go through this Flask proxy. Each command succeeds even without upstream access thanks to built-in fallback data. Remove the `| jq` if you do not have `jq` installed.

## 1. Filter locations by parameter (PM₂.₅)
```bash
curl -s \
  "http://127.0.0.1:8000/locations?parameters_id=2&limit=5" \
  | jq
```

## 2. Find locations near a point (coordinates + radius in meters)
```bash
curl -s \
  "http://127.0.0.1:8000/locations?coordinates=136.90610,35.14942&radius=12000&limit=5" \
  | jq
```

## 3. Find locations in a bounding box (xmin,ymin,xmax,ymax)
```bash
curl -s \
  "http://127.0.0.1:8000/locations?bbox=-118.668153,33.703935,-118.155358,34.337306&limit=5" \
  | jq
```

## 4. Fetch original measurements for a specific sensor (e.g., sensor 3917)
```bash
curl -s \
  "http://127.0.0.1:8000/sensors/3917/measurements?limit=5" \
  | jq
```

## 5. Fetch daily averages for a sensor
```bash
curl -s \
  "http://127.0.0.1:8000/sensors/3917/days?limit=7" \
  | jq
```

## 6. Fetch yearly averages for a sensor
```bash
curl -s \
  "http://127.0.0.1:8000/sensors/3917/days/yearly?limit=3" \
  | jq
```

## 7. Get the latest PM₂.₅ values
```bash
curl -s \
  "http://127.0.0.1:8000/parameters/2/latest?limit=3" \
  | jq
```
