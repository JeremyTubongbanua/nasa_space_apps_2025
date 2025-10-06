from typing import Iterable, Optional

import pandas as pd
import requests

# A set of known air quality parameters.
AIR_QUALITY_PARAMS = {
    'pm10',
    'pm2_5',
    'carbon_monoxide',
    'nitrogen_dioxide',
    'sulphur_dioxide',
    'ozone',
    'aerosol_optical_depth',
    'dust',
    'uv_index',
    'ammonia',
    'alder_pollen',
    'birch_pollen',
    'grass_pollen',
    'mugwort_pollen',
    'olive_pollen',
    'ragweed_pollen',
    'us_aqi',
}

FORECAST_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_ENDPOINTS: Iterable[str] = (
    "https://air-quality-api.open-meteo.com/v1/air-quality",
    "https://api.open-meteo.com/v1/air-quality",
)

def get_weather_data(latitude, longitude, **kwargs):
    """
    Fetches weather or air quality data, handling potential upstream API errors gracefully.
    """
    
    def _split_params(key: str) -> Iterable[str]:
        raw = kwargs.get(key, '')
        return [value for value in raw.split(',') if value]

    requested_params = set(_split_params('hourly'))
    requested_params.update(_split_params('daily'))
    requested_params.update(_split_params('current'))

    use_air_quality_api = any(param in AIR_QUALITY_PARAMS for param in requested_params)

    if use_air_quality_api:
        base_urls: Iterable[str] = AIR_QUALITY_ENDPOINTS
    else:
        base_urls = (FORECAST_ENDPOINT,)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto"
    }
    params.update(kwargs)

    response: Optional[requests.Response] = None
    last_error: Optional[requests.Response] = None
    last_exception: Optional[Exception] = None
    for candidate_url in base_urls:
        try:
            response = requests.get(candidate_url, params=params)
        except requests.RequestException as exc:  # connection errors, timeouts, etc.
            last_exception = exc
            continue
        if response.ok:
            break
        last_error = response
    else:
        error_payload = {
            "error": "Failed to fetch data from Open-Meteo API",
        }
        if last_error is not None:
            error_payload.update(
                {
                    "status_code": last_error.status_code,
                    "reason": last_error.reason,
                    "url_called": last_error.url,
                }
            )
        elif last_exception is not None:
            error_payload.update({"reason": str(last_exception)})
        return error_payload

    if response is None:
        return {"error": "Open-Meteo request aborted before receiving a response"}

    data = response.json()
    processed_data = {}

    if 'hourly' in data:
        hourly_df = pd.DataFrame(data['hourly'])
        processed_data['hourly'] = hourly_df.to_dict('records')

    if 'daily' in data:
        daily_df = pd.DataFrame(data['daily'])
        processed_data['daily'] = daily_df.to_dict('records')

    if 'current' in data:
        processed_data['current'] = data['current']

    processed_data['meta'] = {
        key: value for key, value in data.items() 
        if key not in ['hourly', 'daily', 'current']
    }

    return processed_data
