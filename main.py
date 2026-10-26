# 1 Import the functions from other files
# imports Python's system module
# Here, it is used to stop the program if something goes wrong
import sys

# imports functions, variables and the custom error class from fetch_data
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

from scoring import add_scores, find_best_window, NoValidWindowError

from output import print_recommendation

# 2 Request the data from the API
# Store the responses returned by the request_weather()
# and the request_air_quality() functions
weather = request_weather()
air = request_air_quality()

# Display the HTTP status of each response
print("Weather status:", weather.status_code)
print("Air quality status:", air.status_code)

# 3 Check whether the API responses are usable
try:
    weather_data = check_response("Weather API", weather, WEATHER_VARIABLES)
    print("Weather data: OK")

    air_data = check_response("Air Quality API", air, AIR_QUALITY_VARIABLES)
    print("Air quality data: OK")

except DataFetchError as e:
    print("ERROR:", e)
    sys.exit(1)  # stop the program: no misleading recommendation

# 4 Convert the data into DataFrames
weather_df = to_dataframe(weather_data)
air_df = to_dataframe(air_data)

# displays the first three rows of each table
print(weather_df.head(3))
print(air_df.head(3))

# 5 Combine the two tables
try:
    combined = combine_data(weather_df, air_df)
except DataFetchError as e:
    print("ERROR:", e)
    sys.exit(1)

# the followings are helping to inspect the combined table
# displays the first five rows by default
print(combined.head()) 
# shows the number of rows and columns
print(combined.shape)
# shows the data type of each column, such as datetime, integer or float
print(combined.dtypes)

# 6 Validate the combined data
# If validation succeeds, the resulting data is stored in validated. 
# If it fails, the program stops and displays the error.
try:
    validated = validate_combined_data(combined)
except DataValidationError as e:
    print("ERROR:", e)
    sys.exit(1)

print("Data validation: PASSED")

# 7 Select the analysis period
start, end = get_analysis_period()
period = validated[(validated["time"] >= start) & (validated["time"] <= end)]
print(f"Analysis period: {start:%H:%M} - {end:%H:%M}")
print(period["data_status"].value_counts())

# 8 Calculate the scores
scored = add_scores(validated)
scored_period = scored[(scored["time"] >= start) & (scored["time"] <= end)]

# This displays selected columns, including the original weather information and the calculated scores.
print(scored_period[[
    "time", "temperature_2m", "precipitation_probability", "european_aqi",
    "temperature_score", "rain_score", "air_quality_score", "total_score",
]])

# 9 Find the best two-hour window
try:
    best_window, all_windows = find_best_window(scored, start, end)
except NoValidWindowError as e:
    print("ERROR:", e)
    sys.exit(1)

# 10 display the results
print(all_windows)
print(
    f"Best two-hour window: {best_window['window_start']:%H:%M}-"
    f"{best_window['window_end']:%H:%M}"
)
print(f"Average outdoor score: {best_window['average_score']:.1f}/100")

print_recommendation(best_window, scored_period)


print(weather.json())
print(air.json())

print(weather.json()["hourly"].keys())
print(weather.json()["hourly"]["time"][:3])
print(weather.json()["hourly"]["temperature_2m"][:3])