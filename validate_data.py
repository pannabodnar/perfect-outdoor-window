import pandas as pd

from fetch_data import TIMEZONE, WEATHER_VARIABLES, AIR_QUALITY_VARIABLES

# Columns that must exist in the combined table
REQUIRED_COLUMNS = ["time"] + WEATHER_VARIABLES + AIR_QUALITY_VARIABLES

# Columns needed to calculate the outdoor score
SCORE_COLUMNS = WEATHER_VARIABLES + AIR_QUALITY_VARIABLES

# Plausible (min, max) values for each variable
VALID_RANGES = {
    "temperature_2m": (-40, 50),             # degrees Celsius
    "precipitation_probability": (0, 100),   # percent
    "precipitation": (0, 200),               # millimetres per hour
    "pm2_5": (0, 1000),                      # micrograms per cubic metre
    "pm10": (0, 1500),                       # micrograms per cubic metre
    "european_aqi": (0, 500),                # index
}

# We recommend windows that end by 22:00
END_HOUR = 22

# Define a custom error: DataValidationError
class DataValidationError(Exception):
    """Raised when the combined dataset is not suitable for the analysis."""

# Define the start and the end of the period
# now is an optional input parameter
# =None means that if no value is provided, now defaults to None
def get_analysis_period(now=None):
    """Return (start, end) of the period to analyse: from the next full hour until 22:00."""
    if now is None:
        # Current local time in Vienna, without timezone info
        # (the API timestamps are local times without timezone info too)
        # pd.Timestamp.now(tz=TIMEZONE) gets the current date and time in that time zone
        # .tz_localize(None) removes the time-zone information from the timestamp
        now = pd.Timestamp.now(tz=TIMEZONE).tz_localize(None)

    # Calculate the start time
    # now.floor("h") rounds down the current time down to the beginning of the current hour
    # pd.Timedelta(hours=1) adds one more hour
    start = now.floor("h") + pd.Timedelta(hours=1)

    # Calculate the end time
    # now.normalize() sets the time to midnight on the same date.
    # pd.Timedelta(hours=END_HOUR) adds 22 hours, because END_HOUR = 22.
    end = now.normalize() + pd.Timedelta(hours=END_HOUR)

    # Check whether any analysis time remains
    # If the next full hour is later than 22:00, there is no valid analysis period left for that day, 
    # so the function raises an error.
    if start > end:
        raise DataValidationError("No hours left in the analysis period for today")

    return start, end

# Next, take the combined DataFrame and checks whether the data is suitable for analysis
def validate_combined_data(df, now=None):
    """Check the combined table and add a 'data_status' column.

    Structural problems raise an error. Missing values do NOT raise an error:
    the hour is marked as 'incomplete' instead (a missing value is not a zero).
    """

    # create a separate copy of the input DataFrame
    # (because we will add an additional coulmn to it which is data_status)
    df = df.copy()

    # 1. All required columns exist
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        raise DataValidationError(f"Missing columns: {missing_columns}")

    # 2. Timestamps are real datetimes and values are numeric
    # Check that time contains real datetimes
    # pd.api.types.is_datetime64_any_dtype(...) is a pandas function 
    # that checks whether the column has a datetime data type
    if not pd.api.types.is_datetime64_any_dtype(df["time"]):
        raise DataValidationError("Column 'time' does not contain valid timestamps")

    # Check that the data values are numeric
    for col in SCORE_COLUMNS:
        try:
            # pd.to_numeric() is a pandas function that attempts to convert the values in a column into numeric data
            # means: convert the column to numeric values and store the result back in that column
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            raise DataValidationError(f"Column '{col}' contains non-numeric values")

    # 3. No duplicate timestamps
    # df["time"] selects the time column
    # .duplicated() checks whether each value has appeared before. It marks repeated values as True
    # .any() checks whether at least one value in the result is True.
    if df["time"].duplicated().any():
        raise DataValidationError("Duplicate timestamps found")

    # 4. Timestamps are in chronological order
    # .is_monotonic_increasing checks whether the values are in non-decreasing order
    if not df["time"].is_monotonic_increasing:
        raise DataValidationError("Timestamps are not in chronological order")

    # 5. Values are plausible (missing values are ignored here)
    # .items() gives us each dictionary entry as a pair: a key and its value.
    # col receives the column name, such as "temperature_2m".
    # (low, high) receives the two limits for that column.
    for col, (low, high) in VALID_RANGES.items():
        # df[col].notna() Checks which observations are not missing
        # This identifies values that are not missing, and outside the allowed range.
        out_of_range = df[col].notna() & ((df[col] < low) | (df[col] > high))
        if out_of_range.any():
            raise DataValidationError(
                f"Column '{col}' has values outside the plausible range [{low}, {high}]"
            )

    # 6. The period we want to analyse is fully covered (are there missing hours?)
    start, end = get_analysis_period(now)
    # pd.date_range() is a pandas function that generates a sequence of dates or times between a start and end point
    expected_hours = pd.date_range(start, end, freq="h")
    # .difference() is a pandas method that identifies 
    # which values are present in the first sequence but absent from the second
    # expected_hours contains every hour we need
    # df["time"] contains the timestamps we actually have in our DataFrame.
    # missing_hours contains the expected timestamps that are absent from our data.
    missing_hours = expected_hours.difference(df["time"])
    # len(missing_hours) returns the number of missing timestamps.
    if len(missing_hours) > 0:
        raise DataValidationError(f"Missing hours in the analysis period: {list(missing_hours)}")

    # 7. Mark hours with missing values as incomplete (never replace them with zero)
    # this creates a new column called data_status and initially assigns "complete" to every row
    df["data_status"] = "complete"
    #.isna() checks which values are missing. It returns True for a missing value and False otherwise
    # .any(axis=1)
    # Checks whether each row contains at least one missing value.
    # axis=1 means we check across the columns of each row.
    # Without it, .any() would check down each column by default.
    # .loc is a pandas accessor used to select rows and columns.
    # Here, it selects: Rows where the missing-value condition is True and the column "data_status".
    # It then assigns "incomplete" to those rows.
    df.loc[df[SCORE_COLUMNS].isna().any(axis=1), "data_status"] = "incomplete"

    # Finally, the function returns the DataFrame with the new data_status column
    return df