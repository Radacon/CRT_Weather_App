import json
import requests
import os
from datetime import datetime
import pytz  # To handle time zone conversion more robustly

# Load settings
with open('settings.json', 'r') as f:
    settings = json.load(f)

API_KEY = settings['api_key']
OUTPUT_PATH = 'weatherdata/regional_weather.json'
LAT_LONS = settings['regional_lat_lons']

# Ensure the output directory exists
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# OpenWeatherMap endpoint
CURRENT_WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

# Fetch weather data for a given latitude and longitude
def fetch_weather(lat, lon):
    params = {
        'lat': lat,
        'lon': lon,
        'appid': API_KEY,
        'units': 'imperial',  # Use 'imperial' for Fahrenheit, mph, etc.
    }
    response = requests.get(CURRENT_WEATHER_URL, params=params)
    response.raise_for_status()
    return response.json()

# Parse weather data to extract required fields
def parse_weather(data):
    weather = {
        'location': data.get('name', 'Unknown'),
        'conditions': data['weather'][0]['description'].capitalize(),
        'temperature': round(data['main']['temp'], 1),
    }
    return weather

# Convert UTC observation time to the system's local time zone
def convert_to_local_time(utc_timestamp):
    # Create a UTC datetime object
    utc_time = datetime.utcfromtimestamp(utc_timestamp).replace(tzinfo=pytz.utc)
    # Convert to local time zone
    local_time = utc_time.astimezone()
    # Format with local time zone abbreviation
    return local_time.strftime('%Y-%m-%d %H:%M:%S %Z')

# Main function to fetch weather for all regional lat/lons
def main():
    print("Fetching regional weather data...")
    regional_weather = []

    # Placeholder for observation time
    observation_time = None

    for entry in LAT_LONS:
        city = entry['city']
        lat = entry['lat']
        lon = entry['lon']

        try:
            print(f"Fetching weather for {city} (Lat: {lat}, Lon: {lon})...")
            raw_data = fetch_weather(lat, lon)
            
            # Set observation time based on the first valid fetch
            if observation_time is None:
                observation_time = convert_to_local_time(raw_data['dt'])

            parsed_data = parse_weather(raw_data)
            regional_weather.append(parsed_data)
        except requests.RequestException as e:
            print(f"Error fetching weather for {city}: {e}")
            regional_weather.append({
                'location': city,
                'conditions': 'Error fetching data',
                'temperature': None,
            })

    # Combine observation time with weather data
    output_data = {
        'observation_time': observation_time,
        'regional_weather': regional_weather,
    }

    # Save the regional weather data to a JSON file
    print("Saving regional weather data to file...")
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=4)

    print("Regional weather data saved successfully.")

if __name__ == "__main__":
    main()
