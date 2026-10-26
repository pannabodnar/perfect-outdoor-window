import pandas as pd


def temperature_score(temp):
    """Temperature score (max 30 points)."""
    # pd.isna() is a pandas function that checks whether a value is missing
    # return ends the function and sends the result back.
    # float("nan") produces a special value called NaN, which represents missing or unknown numeric data.
    if pd.isna(temp):
        return float("nan")  # missing value: we do not know, so no score
    if 15 <= temp <= 25:
        return 30
    if 10 <= temp < 15 or 25 < temp <= 30:
        return 20
    return 0


def rain_score(prob):
    """Rain score based on precipitation probability in % (max 30 points)."""
    if pd.isna(prob):
        return float("nan")
    if prob <= 10:
        return 30
    if prob <= 30:
        return 20
    if prob <= 60:
        return 10
    return 0


def air_quality_score(aqi):
    """Air quality score based on the European AQI (max 40 points)."""
    if pd.isna(aqi):
        return float("nan")
    if aqi <= 20:
        return 40
    if aqi <= 40:
        return 30
    if aqi <= 60:
        return 15
    if aqi <= 80:
        return 5
    return 0


def add_scores(df):
    """Add the component scores and the total hourly score (0-100) to the table."""
    df = df.copy()

    # df["temperature_2m"] selects the temperature column
    # .apply(temperature_score) applies our previously defined temperature_score() function to every value in that column
    # df["temperature_score"] = saves the resulting scores in a new column.
    df["temperature_score"] = df["temperature_2m"].apply(temperature_score)
    df["rain_score"] = df["precipitation_probability"].apply(rain_score)
    df["air_quality_score"] = df["european_aqi"].apply(air_quality_score)

    # Calculate the total hourly score
    # A sum with a missing component stays missing (NaN), it is never treated as 0
    df["total_score"] = (
        df["temperature_score"] + df["rain_score"] + df["air_quality_score"]
    )

    # Hours marked as incomplete in Step 4 never get a total score
    # .loc is a pandas accessor used to select specific rows and columns
    # It selects rows where data_status equals "incomplete" and the total_score column
    #It then sets the total score to NaN for those rows.
    df.loc[df["data_status"] == "incomplete", "total_score"] = float("nan")

    # Finally, the function returns the modified DataFrame, now containing the three component scores and the total score
    return df

WINDOW_HOURS = 2  # length of the recommended window (agreed with the group)


class NoValidWindowError(Exception):
    """Raised when no reliable window can be recommended."""


def find_best_window(df, start, end, window_hours=WINDOW_HOURS):
    """Find the window of consecutive hours with the highest average score.

    Only hours between 'start' and 'end' are used, so a window always ends by 'end'.
    Windows that contain missing scores or missing hours are never considered.
    Returns the best window and the table of all valid windows.
    """
    # Hours that can be part of a window: from start until end (end excluded,
    # because the hour starting at 22:00 would end after 22:00)

    # This line filters the DataFrame, keeping only rows whose timestamps fall within the analysis period
    period = df[(df["time"] >= start) & (df["time"] < end)]
    # .sort_values("time"): sorts the rows according to the time column, from earliest to latest
    # .reset_index(drop=True): resets the row index after filtering and sorting.
    period = period.sort_values("time").reset_index(drop=True)


    # create an empty list (windows is a variable)
    windows = []
    # Loop through all possible windows
    # len(period) returns the number of rows in our period DataFrame.
    # window_hours is the length of each window. By default, it is 2.
    # range(...) generates the sequence of numbers used by the loop.
    # i is the variable that represents the current starting position.
    for i in range(len(period) - window_hours + 1):
        # Here, we select the rows belonging to the current window and store them in a variable called block.
        block = period.iloc[i:i + window_hours]

        # Skip blocks whose hours are not consecutive (a missing hour in between)
        # .diff() is a pandas method that calculates the difference between each timestamp and the previous timestamp
        # .dropna() Removes the missing difference from the first row, leaving only the differences we can check.
        gaps = block["time"].diff().dropna()
        # pd.Timedelta() is a pandas function for representing a duration of time. Here, it represents exactly one hour.
        # .all() is a pandas method that returns True only if every value in the condition is True.
        if not (gaps == pd.Timedelta(hours=1)).all():
            # continue skips the rest of the current loop iteration and moves on to the next possible window.
            continue

        # Skip blocks with a missing score (incomplete data)
        #- block["total_score"] selects the total-score column for the current window.
        # .isna() checks which scores are missing.
        # .any() checks whether at least one score is missing.
        if block["total_score"].isna().any():
            # continue skips the current window if a missing score exists
            continue

        # Record the starting time of the current window
        #block["time"] selects its time column
        # .iloc[0] selects the first row by position
        window_start = block["time"].iloc[0]
        # .append() is a Python list method that adds a new item to the end of a list.
        # Here, the item is a dictionary containing three pieces of information (window start, window end and average score)
        windows.append({
            "window_start": window_start,
            "window_end": window_start + pd.Timedelta(hours=window_hours),
            "average_score": block["total_score"].mean(),
        })

    # Check whether we found any valid windows
    # earlier we created an empty list: window = []
    # As the function runs, it adds valid windows to this list using .append()
    # If the list is empty, not windows evaluates to True
    if not windows:
        raise NoValidWindowError("No valid window: not enough complete consecutive hours")

    # Convert the list into a DataFrame
    windows = pd.DataFrame(windows)

    # Highest average first; if two windows tie, the earlier one wins
    # False for average_score means highest score first.
    # True for window_start means earliest starting time first.
    windows = windows.sort_values(
        ["average_score", "window_start"], ascending=[False, True]
    # After sorting, the original row indices might no longer be in order
    # .reset_index() creates a fresh index starting at 0
    # drop=True discards the old index instead of keeping it as an extra column
    ).reset_index(drop=True)

    # The first row of the sorted DataFrame — the best window, 
    # because it has the highest average score and wins any tie-break.
    return windows.iloc[0], windows