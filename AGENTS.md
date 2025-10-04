# AGENTS.md

We're going to make a web-based dashboard that is essentially a "data aggregator." We're going to take datapoints from multiple APIs (OpenAQ, TEMPO, and local weather) then aggregate it into one dashboard that's easy to use. It'll let the user make an account, input their location, then subscribe to different events (e.g. give me a text notification when the Air Pollution exceeds 10 AQI). 

The multiple components that people could work on are:

Dashboard design (Figma)
Website implementation (React)
OAuth (Sign in with Google)
Backend API Aggregation (Python)
SMS Notifications (Twilio)
Video/Editing (Post on YouTube)

## APIs

Here are the 3 core APIs I’d use for your stack:
	1.	OpenAQ v3 (ground sensors & AQI-ish raw pollutants)

	•	Use for: Historical + recent NO₂, O₃, PM2.5, PM10, NOx at station level.
	•	Why: Free, global, JSON, great for validation against TEMPO and for local baselines.
	•	Key endpoints:
	•	Measurements:
GET https://api.openaq.org/v3/measurements?parameters=pm25,no2,o3&coordinates={lat},{lon}&radius=25000&date_from=...&date_to=...&limit=1000
	•	Latest per location:
GET https://api.openaq.org/v3/latest?coordinates={lat},{lon}&radius=25000&parameters=pm25,no2,o3
	•	Notes: Values often in µg/m³ (PM) and ppb/ppm (gases) — normalize units for your alerts.

	2.	NASA TEMPO via Earthdata + Harmony (satellite trace gases, hourly NRT)

	•	Use for: Hourly NO₂, HCHO (formaldehyde), Aerosol Index over North America, to add satellite context/features for your forecast.
	•	Why: Challenge requires TEMPO; Harmony lets you subset/reproject/convert to cloud-friendly outputs programmatically.
	•	Flow:
	•	Get Earthdata Login.
	•	Discover TEMPO collection ID (CMR).
	•	Submit a Harmony request (clip to user bbox & time window) and poll job status.
	•	Example (conceptual request body):
	•	Collection: tempo_<collection_id>
	•	Params: bbox, time range, output: zarr or netcdf4
	•	Notes: Cache preprocessed tiles by city/zoom to keep your backend fast.

	3.	Open-Meteo Weather API (free, no key; forecast + reanalysis)

	•	Use for: Weather drivers your model/alerts need: wind speed/dir, temperature, humidity, boundary-layer proxies (mixing height via “forecast_meteo” or “air_quality” endpoints if needed).
	•	Why: Fast, CORS-friendly, simple JSON; good for both current + forecast.
	•	Example:

https://api.open-meteo.com/v1/forecast
  ?latitude={lat}&longitude={lon}
  &hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m
  &forecast_days=3


	•	Notes: If you want Canada-specific official sources later, you can add Environment Canada (ECCC) feeds, but Open-Meteo is perfect for MVP.

⸻

How these map to your plan
	•	Backend API Aggregation (Python):
	•	Fetch OpenAQ (ground), Harmony/TEMPO (satellite), Open-Meteo (weather).
	•	Normalize timestamps/units → compute AQI or thresholds → store in Postgres.
	•	Alerts (Twilio):
	•	Trigger when normalized metric crosses user-defined thresholds (e.g., PM2.5 > 10 µg/m³ or NO₂ > X ppb).
	•	Frontend (React):
	•	Map layer: TEMPO overlay (processed via Harmony) + station pins (OpenAQ).
	•	Charts: combined hourly forecast from Open-Meteo + predicted AQ.
	•	OAuth: Google Identity Services for sign-in.

If you want, I can sketch the exact data model + cron flow (ETL cadence, caching strategy, and a minimal FastAPI router) to wire these three together quickly.