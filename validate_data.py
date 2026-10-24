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


class DataValidationError(Exception):
    """Raised when the combined dataset is not suitable for the analysis."""


def get_analysis_period(now=None):
    """Return (start, end) of the period to analyse: from the next full hour until 22:00."""
    if now is None:
        # Current local time in Vienna, without timezone info
        # (the API timestamps are local times without timezone info too)
        now = pd.Timestamp.now(tz=TIMEZONE).tz_localize(None)

    start = now.floor("h") + pd.Timedelta(hours=1)
    end = now.normalize() + pd.Timedelta(hours=END_HOUR)

    if start > end:
        raise DataValidationError("No hours left in the analysis period for today")

    return start, end


def validate_combined_data(df, now=None):
    """Check the combined table and add a 'data_status' column.

    Structural problems raise an error. Missing values do NOT raise an error:
    the hour is marked as 'incomplete' instead (a missing value is not a zero).
    """
    df = df.copy()

    # 1. All required columns exist
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        raise DataValidationError(f"Missing columns: {missing_columns}")

    # 2. Timestamps are real datetimes and values are numeric
    if not pd.api.types.is_datetime64_any_dtype(df["time"]):
        raise DataValidationError("Column 'time' does not contain valid timestamps")

    for col in SCORE_COLUMNS:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            raise DataValidationError(f"Column '{col}' contains non-numeric values")

    # 3. No duplicate timestamps
    if df["time"].duplicated().any():
        raise DataValidationError("Duplicate timestamps found")

    # 4. Timestamps are in chronological order
    if not df["time"].is_monotonic_increasing:
        raise DataValidationError("Timestamps are not in chronological order")

    # 5. Values are plausible (missing values are ignored here)
    for col, (low, high) in VALID_RANGES.items():
        out_of_range = df[col].notna() & ((df[col] < low) | (df[col] > high))
        if out_of_range.any():
            raise DataValidationError(
                f"Column '{col}' has values outside the plausible range [{low}, {high}]"
            )

    # 6. The period we want to analyse is fully covered
    start, end = get_analysis_period(now)
    expected_hours = pd.date_range(start, end, freq="h")
    missing_hours = expected_hours.difference(df["time"])
    if len(missing_hours) > 0:
        raise DataValidationError(f"Missing hours in the analysis period: {list(missing_hours)}")

    # 7. Mark hours with missing values as incomplete (never replace them with zero)
    df["data_status"] = "complete"
    df.loc[df[SCORE_COLUMNS].isna().any(axis=1), "data_status"] = "incomplete"

    return df