import sys
from fetch_data import (
    request_weather,
    request_air_quality,
    check_response,
    DataFetchError,
    WEATHER_VARIABLES,
    AIR_QUALITY_VARIABLES,
)


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


print(weather.json())
print(air.json())

print(weather.json()["hourly"].keys())
print(weather.json()["hourly"]["time"][:3])
print(weather.json()["hourly"]["temperature_2m"][:3])