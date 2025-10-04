import requests
import pandas as pd

# A set of known air quality parameters.
AIR_QUALITY_PARAMS = {
    'pm10', 'pm2_5', 'carbon_monoxide', 'nitrogen_dioxide', 'sulphur_dioxide', 
    'ozone', 'aerosol_optical_depth', 'dust', 'uv_index', 'ammonia', 'alder_pollen', 
    'birch_pollen', 'grass_pollen', 'mugwort_pollen', 'olive_pollen', 'ragweed_pollen'
}

def get_weather_data(latitude, longitude, **kwargs):
    """
    Fetches weather or air quality data, handling potential upstream API errors gracefully.
    """
    
    requested_params = set(kwargs.get('hourly', '').split(',') + kwargs.get('daily', '').split(','))
    
    use_air_quality_api = any(param in AIR_QUALITY_PARAMS for param in requested_params)
    
    if use_air_quality_api:
        base_url = "https://api.open-meteo.com/v1/air-quality"
    else:
        base_url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto"
    }
    params.update(kwargs)

    response = requests.get(base_url, params=params)

    # Gracefully handle HTTP errors instead of crashing
    if not response.ok:
        return {
            "error": "Failed to fetch data from Open-Meteo API",
            "status_code": response.status_code,
            "reason": response.reason,
            "url_called": response.url
        }
    
    data = response.json()
    processed_data = {}

    if 'hourly' in data:
        hourly_df = pd.DataFrame(data['hourly'])
        processed_data['hourly'] = hourly_df.to_dict('records')

    if 'daily' in data:
        daily_df = pd.DataFrame(data['daily'])
        processed_data['daily'] = daily_df.to_dict('records')

    processed_data['meta'] = {
        key: value for key, value in data.items() 
        if key not in ['hourly', 'daily']
    }

    return processed_data