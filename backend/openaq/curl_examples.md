# OpenAQ `curl` Examples

Here’s the quickest, real-world way to pull Toronto air data from OpenAQ v3 using curl. Replace $OPENAQ_KEY with your key (or export it once).

0) Auth header

Assume OPENAQ_KEY is an environment variable in my system already.

1) Find monitoring locations in/around Toronto

Use a point+radius (25 km around downtown) or a bounding box.

# Point + radius (Downtown Toronto ≈ 43.651,-79.347; 25 km)
curl -s 'https://api.openaq.org/v3/locations?coordinates=43.651,-79.347&radius=25000&limit=50' \
  -H "X-API-Key: $OPENAQ_KEY" | jq '.results[] | {id,name,coordinates,timezone}'

# Bounding box (~GTA): minLon,minLat,maxLon,maxLat
curl -s 'https://api.openaq.org/v3/locations?bbox=-79.8,43.4,-79.0,43.9&limit=50' \
  -H "X-API-Key: $OPENAQ_KEY" | jq '.results[] | {id,name,coordinates,timezone}'

Both coordinates+radius and bbox are supported geospatial filters. (Don’t combine them in one call.)  ￼

⸻

2) List a location’s sensors (to see what pollutants are available)

Pick a locations_id from step 1 (example id shown as 12345):

curl -s 'https://api.openaq.org/v3/locations/12345/sensors' \
  -H "X-API-Key: $OPENAQ_KEY" | jq '.results[] | {sensors_id: .id, parameter: .parameter.name, units: .parameter.units}'

A sensor measures one parameter (e.g., PM2.5, NO₂) at that location.  ￼

⸻

3) Get the latest readings for that location

curl -s 'https://api.openaq.org/v3/locations/12345/latest' \
  -H "X-API-Key: $OPENAQ_KEY" | jq '.results[] | {parameter: .parameter.name, value, unit, datetime: .datetime}'

This returns the most recent value per parameter for the station.  ￼

⸻

4) Get time-series measurements (per sensor)

Grab a sensors_id from step 2 (example 67890). Query a date range (UTC ISO-8601 is fine):

# Raw measurements in a window (e.g., last 7 days)
curl -s 'https://api.openaq.org/v3/sensors/67890/measurements?date_from=2025-09-27T00:00:00Z&date_to=2025-10-04T00:00:00Z&limit=1000' \
  -H "X-API-Key: $OPENAQ_KEY" | jq '.results[] | {datetime, value, unit}'

# Aggregated daily values (same window)
curl -s 'https://api.openaq.org/v3/sensors/67890/days?date_from=2025-09-27&date_to=2025-10-04' \
  -H "X-API-Key: $OPENAQ_KEY" | jq '.results[] | {date, value, unit}'

Use date_from/date_to and keep windows modest to avoid timeouts; aggregation endpoints (/hours, /days) are available per sensor. Timestamps follow ISO-8601.  ￼

⸻

5) (Optional) Discover parameters supported

curl -s 'https://api.openaq.org/v3/parameters' \
  -H "X-API-Key: $OPENAQ_KEY" | jq '.results[] | {id,name,displayName,units}'

Useful to map names like pm25, pm10, no2, o3, etc.  ￼

⸻

What you’ll get
	•	Station metadata (name, lat/lon, timezone, provider) from Locations.  ￼
	•	The newest values per pollutant from Latest.  ￼
	•	High-resolution time series (or hourly/daily rollups) from Measurements (per Sensor).  ￼

If you want, tell me roughly where in Toronto (or just use your device’s lat/lon), and I’ll run the exact bbox/coordinates you’d use.