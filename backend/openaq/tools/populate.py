
import csv
import os
import requests
from datetime import datetime, timedelta

# Configuration
# The API key is expected to be set as an environment variable.
API_KEY = os.environ.get("OPENAQ_KEY")
BASE_URL = "https://api.openaq.org/v3/sensors"
# The script is in /tools, so the data file is at ../data/sensors.csv
SENSORS_CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/sensors.csv')

def fetch_sensor_data(sensor_id: int, date_from: str, date_to: str):
    """
    Fetches time-series measurements for a given sensor ID within a date range.
    """
    if not API_KEY:
        print("Error: OPENAQ_KEY environment variable not set.")
        return None

    headers = {"X-API-Key": API_KEY}
    url = f"{BASE_URL}/{sensor_id}/measurements"
    params = {
        "date_from": date_from,
        "date_to": date_to,
        "limit": 1000  # Adjust limit as needed
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for sensor {sensor_id}: {e}")
        return None

def main():
    """
    Main function to read sensor IDs from a CSV and fetch their data.
    """
    print(f"Reading sensors from {SENSORS_CSV_PATH}...")

    try:
        with open(SENSORS_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header row
            print(f"CSV Header: {header}")

            # Define the date range for the query (e.g., last 7 days)
            date_to = datetime.utcnow()
            date_from = date_to - timedelta(days=7)
            date_to_iso = date_to.isoformat() + "Z"
            date_from_iso = date_from.isoformat() + "Z"

            print(f"Fetching data from {date_from_iso} to {date_to_iso}")

            for row in reader:
                try:
                    sensor_id = int(row[0])
                    sensor_name = row[1]
                    print(f"\n--- Processing Sensor ID: {sensor_id} ({sensor_name}) ---")

                    data = fetch_sensor_data(sensor_id, date_from_iso, date_to_iso)

                    if data and data.get('results'):
                        print(f"  Successfully fetched {len(data['results'])} records.")
                        # You can process or save the data here. For now, just print a summary.
                        for result in data['results'][:3]: # Print first 3 results as a sample
                            print(f"    - {result}")
                    else:
                        print("  No data returned or an error occurred.")

                except (ValueError, IndexError) as e:
                    print(f"Skipping row due to parsing error: {row} ({e})")

    except FileNotFoundError:
        print(f"Error: The file {SENSORS_CSV_PATH} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
