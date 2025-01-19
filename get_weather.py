import json
import requests
import os
from datetime import datetime, timezone, timedelta
import time
import pytz

# Load settings
with open('settings.json', 'r') as f:
    settings = json.load(f)

API_KEY = settings['api_key']
LAT = settings['lat']
LON = settings['lon']
OUTPUT_PATH = 'weatherdata/home_weather.json'
ICON_DIR = 'weatherdata/icons/'

# Ensure directories exist
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
os.makedirs(ICON_DIR, exist_ok=True)

# OpenWeatherMap endpoints
CURRENT_WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

# Convert wind direction from degrees to cardinal directions
def wind_direction_cardinal(degrees):
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    index = round(degrees / 45) % 8
    return directions[index]

# Calculate dew point
def calculate_dew_point(temp, humidity):
    temp_c = (temp - 32) * 5 / 9  # Convert Fahrenheit to Celsius
    a = 17.27
    b = 237.7
    alpha = (a * temp_c) / (b + temp_c) + (humidity / 100.0)
    dew_point_c = (b * alpha) / (a - alpha)
    dew_point_f = dew_point_c * 9 / 5 + 32  # Convert Celsius back to Fahrenheit
    return round(dew_point_f, 2)

# Fetch current weather data
def fetch_weather():
    params = {
        'lat': LAT,
        'lon': LON,
        'appid': API_KEY,
        'units': 'imperial',  # Use 'imperial' for Fahrenheit, mph, etc.
    }

    response = requests.get(CURRENT_WEATHER_URL, params=params)
    response.raise_for_status()
    return response.json()

# Convert UTC observation time to the system's local time zone
def convert_to_local_time(utc_timestamp):
    # Create a UTC datetime object
    utc_time = datetime.utcfromtimestamp(utc_timestamp).replace(tzinfo=pytz.utc)
    # Convert to local time zone
    local_time = utc_time.astimezone()
    # Format with local time zone abbreviation
    return local_time.strftime('%Y-%m-%d %H:%M:%S %Z')

# Parse weather data
def parse_weather(data):
    # Read previous pressure from output file if it exists
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, 'r') as f:
            previous_data = json.load(f)
            previous_pressure = previous_data.get('pressure_inhg', None)
    else:
        previous_pressure = None

    current_pressure = data['main']['pressure'] * 0.02953  # Convert hPa to inHg
    pressure_trend = "steady"

    if previous_pressure is not None:
        if current_pressure > previous_pressure:
            pressure_trend = "up"
        elif current_pressure < previous_pressure:
            pressure_trend = "down"

    temperature = data['main']['temp']
    humidity = data['main']['humidity']

    observation_time = convert_to_local_time(data['dt'])

    weather = {
        'temperature': temperature,
        'conditions': data['weather'][0]['description'],
        'wind_speed_mph': data['wind'].get('speed', 0),
        'wind_direction': wind_direction_cardinal(data['wind'].get('deg', 0)),
        'gusts_mph': data['wind'].get('gust', 0),
        'humidity_percent': humidity,
        'dewpoint': calculate_dew_point(temperature, humidity),
        'ceiling_feet': data.get('clouds', {}).get('all', 0) * 100,
        'visibility_miles': data.get('visibility', 0) / 1609.34,
        'pressure_inhg': current_pressure,
        'pressure_trend': pressure_trend,
        'icon_url': f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
        'observation_time': observation_time,  # Include time zone
        'location': data.get('name', 'Unknown'),
    }
    return weather


# Save weather icon
# Save weather icon only if it doesn't already exist
def save_icon(icon_url, icon_name):
    icon_path = os.path.join(ICON_DIR, icon_name)
    if os.path.exists(icon_path):
        print(f"Icon '{icon_name}' already exists. Skipping download.")
        return
    try:
        print(f"Downloading icon: {icon_name}")
        response = requests.get(icon_url)
        response.raise_for_status()
        with open(icon_path, 'wb') as f:
            f.write(response.content)
        print(f"Icon '{icon_name}' downloaded successfully.")
    except requests.RequestException as e:
        print(f"Error downloading icon '{icon_name}': {e}")


# Main function
def main():
    print("Fetching weather data...")
    weather_data = fetch_weather()

    print("Parsing weather data...")
    parsed_data = parse_weather(weather_data)

    print("Saving weather data to file...")
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(parsed_data, f, indent=4)

    print("Downloading weather icon...")
    icon_name = f"{parsed_data['icon_url'].split('/')[-1]}"
    save_icon(parsed_data['icon_url'], icon_name)

    print("Weather data and icon saved successfully.")

if __name__ == "__main__":
    main()
