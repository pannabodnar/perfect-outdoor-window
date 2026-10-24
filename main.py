import sys
from fetch_data import (
    request_weather,
    request_air_quality,
    check_response,
    DataFetchError,
    WEATHER_VARIABLES,
    AIR_QUALITY_VARIABLES,
    to_dataframe,
    combine_data,
)

from validate_data import validate_combined_data, get_analysis_period, DataValidationError

weather = request_weather()
air = request_air_quality()

print("Weather status:", weather.status_code)
print("Air quality status:", air.status_code)

try:
    weather_data = check_response("Weather API", weather, WEATHER_VARIABLES)
    print("Weather data: OK")

    air_data = check_response("Air Quality API", air, AIR_QUALITY_VARIABLES)
    print("Air quality data: OK")

except DataFetchError as e:
    print("ERROR:", e)
    sys.exit(1)  # stop the program: no misleading recommendation


weather_df = to_dataframe(weather_data)
air_df = to_dataframe(air_data)

print(weather_df.head(3))
print(air_df.head(3))

try:
    combined = combine_data(weather_df, air_df)
except DataFetchError as e:
    print("ERROR:", e)
    sys.exit(1)

print(combined.head())
print(combined.shape)
print(combined.dtypes)

try:
    validated = validate_combined_data(combined)
except DataValidationError as e:
    print("ERROR:", e)
    sys.exit(1)

print("Data validation: PASSED")

start, end = get_analysis_period()
period = validated[(validated["time"] >= start) & (validated["time"] <= end)]
print(f"Analysis period: {start:%H:%M} - {end:%H:%M}")
print(period["data_status"].value_counts())




print(weather.json())
print(air.json())

print(weather.json()["hourly"].keys())
print(weather.json()["hourly"]["time"][:3])
print(weather.json()["hourly"]["temperature_2m"][:3])