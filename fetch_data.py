import requests

#parameters
LATITUDE = 48.210033
LONGITUDE = 16.363449 #from https://www.latlong.net/place/vienna-austria-4542.html
TIMEZONE = "Europe/Berlin"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def request_weather():
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "temperature_2m,precipitation_probability,precipitation",
        "timezone": TIMEZONE,
        "forecast_days": 1,
    }
    response = requests.get(WEATHER_URL, params=params, timeout=10)
    return response


def request_air_quality():
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "pm2_5,pm10,european_aqi",
        "timezone": TIMEZONE,
        "forecast_days": 1,
    }
    response = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
    return response