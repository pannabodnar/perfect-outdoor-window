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