import pandas as pd


def temperature_score(temp):
    """Temperature score (max 30 points)."""
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

    df["temperature_score"] = df["temperature_2m"].apply(temperature_score)
    df["rain_score"] = df["precipitation_probability"].apply(rain_score)
    df["air_quality_score"] = df["european_aqi"].apply(air_quality_score)

    # A sum with a missing component stays missing (NaN), it is never treated as 0
    df["total_score"] = (
        df["temperature_score"] + df["rain_score"] + df["air_quality_score"]
    )

    # Hours marked as incomplete in Step 4 never get a total score
    df.loc[df["data_status"] == "incomplete", "total_score"] = float("nan")

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
    period = df[(df["time"] >= start) & (df["time"] < end)]
    period = period.sort_values("time").reset_index(drop=True)

    windows = []
    for i in range(len(period) - window_hours + 1):
        block = period.iloc[i:i + window_hours]

        # Skip blocks whose hours are not consecutive (a missing hour in between)
        gaps = block["time"].diff().dropna()
        if not (gaps == pd.Timedelta(hours=1)).all():
            continue

        # Skip blocks with a missing score (incomplete data)
        if block["total_score"].isna().any():
            continue

        window_start = block["time"].iloc[0]
        windows.append({
            "window_start": window_start,
            "window_end": window_start + pd.Timedelta(hours=window_hours),
            "average_score": block["total_score"].mean(),
        })

    if not windows:
        raise NoValidWindowError("No valid window: not enough complete consecutive hours")

    windows = pd.DataFrame(windows)

    # Highest average first; if two windows tie, the earlier one wins
    windows = windows.sort_values(
        ["average_score", "window_start"], ascending=[False, True]
    ).reset_index(drop=True)

    return windows.iloc[0], windows