import pandas as pd

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

WEATHER_VARIABLES = ["temperature_2m", "precipitation_probability", "precipitation"]
AIR_QUALITY_VARIABLES = ["pm2_5", "pm10", "european_aqi"]


class DataFetchError(Exception):
    """Raised when an API response cannot be used."""


def check_response(name, response, variables):
    """Check an API response and return its JSON content if it is valid."""

    # 1. Was the request successful?
    if response.status_code != 200:
        raise DataFetchError(f"{name}: HTTP status {response.status_code}")

    # 2. Is the response readable JSON?
    try:
        data = response.json()
    except ValueError:
        raise DataFetchError(f"{name}: response is not valid JSON")

    # 3. Is the hourly section present?
    hourly = data.get("hourly")
    if not hourly:
        raise DataFetchError(f"{name}: 'hourly' section is missing")

    # 4. Are all the expected variables present?
    missing = [v for v in ["time"] + variables if v not in hourly]
    if missing:
        raise DataFetchError(f"{name}: missing variables: {missing}")

    # 5. Is the hourly data empty?
    n_hours = len(hourly["time"])
    if n_hours == 0:
        raise DataFetchError(f"{name}: hourly data is empty")

    # 6. Do all variables have the same length as 'time'?
    for v in variables:
        if len(hourly[v]) != n_hours:
            raise DataFetchError(f"{name}: '{v}' has a different length than 'time'")

    return data


def to_dataframe(data):
    """Convert the 'hourly' section of an API response into a DataFrame."""
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])  # text -> real timestamps
    return df


def combine_data(weather_df, air_df):
    """Combine the weather and air quality tables using their timestamps."""

    # Do not assume the two responses match: check that they refer
    # to exactly the same local hours before combining them
    if not weather_df["time"].equals(air_df["time"]):
        raise DataFetchError("Weather and air quality timestamps do not match")

    # validate="one_to_one" raises an error if a timestamp is duplicated
    return weather_df.merge(air_df, on="time", how="inner", validate="one_to_one")