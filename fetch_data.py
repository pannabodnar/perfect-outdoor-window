# Import pandas to organise and analyse data in tables.
import pandas as pd

# Import requests to send HTTP requests to external APIs 
# and retrieve weather and air quality forecast data.
import requests

# define the parameters
# setting the location to vienna
LATITUDE = 48.210033
LONGITUDE = 16.363449 #from https://www.latlong.net/place/vienna-austria-4542.html
TIMEZONE = "Europe/Berlin"

# Store the URL of the Open-Meteo Weather Forecast API.
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Store the URL of the Open-Meteo Air Quality API.
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Define a function that requests weather forecast data
def request_weather():
     # Create a dictionary containing the parameters
     # that will be sent to the weather API.
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "temperature_2m,precipitation_probability,precipitation",
        "timezone": TIMEZONE,
        "forecast_days": 1,
    }
    # Send an HTTP GET request to the weather API using the
    # specified URL and parameters. Stop waiting if the request
    # takes longer than 10 seconds.
    response = requests.get(WEATHER_URL, params=params, timeout=10)
    # Return the API response to the function's caller.
    return response

# Define a function that requests air quality forecast data
def request_air_quality():
     # Create a dictionary containing the parameters
     # that will be sent to the air quality API.
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "pm2_5,pm10,european_aqi",
        "timezone": TIMEZONE,
        "forecast_days": 1,
    }
    # Send an HTTP GET request to the air quality API using the
    # specified URL and parameters. Stop waiting if the request
    # takes longer than 10 seconds.
    response = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
    # Return the API response to the function's caller.
    return response

# Define the weather variables that the API response must contain.
WEATHER_VARIABLES = ["temperature_2m", "precipitation_probability", "precipitation"]
# Define the air quality variables that the API response must contain.
AIR_QUALITY_VARIABLES = ["pm2_5", "pm10", "european_aqi"]

# Define a custom error for problems that occur when
# retrieving or checking data from an API.
# Exception is Python's built in base class for errors
class DataFetchError(Exception):
    """Raised when an API response cannot be used."""

# Define a function that checks whether an API response
# is successful and contains the expected data.
def check_response(name, response, variables):
    """Check an API response and return its JSON content if it is valid."""

    # 1. Was the request successful? 
    # 200 status code means that the request was successful
    if response.status_code != 200:
        raise DataFetchError(f"{name}: HTTP status {response.status_code}")

    # 2. Is the response readable JSON?
    # we check whether the response contains data that Python can read as JSON.
    try:
        data = response.json()
    except ValueError:
        raise DataFetchError(f"{name}: response is not valid JSON")

    # 3. Is the hourly section present?
    # The .get() method retrieves the value associated with the "hourly" key.
    # If the key does not exist, it returns None instead of raising a KeyError.
    hourly = data.get("hourly")
    if not hourly:
        raise DataFetchError(f"{name}: 'hourly' section is missing")

    # 4. Are all the expected variables present?
    # Combine the required "time" key with the variables passed
    # to the function, then collect any keys that are missing.
    missing = [v for v in ["time"] + variables if v not in hourly]
    if missing:
        raise DataFetchError(f"{name}: missing variables: {missing}")

    # 5. Is the hourly data empty?
    # Count how many time points are available in the API response.
    n_hours = len(hourly["time"])
    # If there are no timestamps, the hourly data is empty
    # and cannot be used for further analysis.
    if n_hours == 0:
        raise DataFetchError(f"{name}: hourly data is empty")

    # 6. Do all variables have the same length as 'time'?
    for v in variables:
        if len(hourly[v]) != n_hours:
            raise DataFetchError(f"{name}: '{v}' has a different length than 'time'")
 # If all checks pass, return the validated API data
 # so that the rest of the program can use it.
    return data


def to_dataframe(data):
    """Convert the 'hourly' section of an API response into a DataFrame."""
     # Extract the hourly forecast data and convert it into a pandas table.
    df = pd.DataFrame(data["hourly"])
     # Convert the time column from text into datetime objects,
     # so that timestamps can be compared and processed correctly.
    df["time"] = pd.to_datetime(df["time"])  # text -> real timestamps
    # Return the DataFrame so that other parts of the program can use it.
    return df


def combine_data(weather_df, air_df):
    """Combine the weather and air quality tables using their timestamps."""

    # Do not assume the two responses match: check that they refer
    # to exactly the same local hours before combining them
    if not weather_df["time"].equals(air_df["time"]):
        raise DataFetchError("Weather and air quality timestamps do not match")

    # validate="one_to_one" raises an error if a timestamp is duplicated
    return weather_df.merge(air_df, on="time", how="inner", validate="one_to_one")