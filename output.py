import pandas as pd

from fetch_data import TIMEZONE

LOCATION_NAME = "Vienna"


def print_recommendation(best_window, hourly_df):
    """Print the final recommendation and the main reason for it."""
    start = best_window["window_start"]
    end = best_window["window_end"]

    # Hours that belong to the recommended window
    hours = hourly_df[(hourly_df["time"] >= start) & (hourly_df["time"] < end)]

    today = pd.Timestamp.now(tz=TIMEZONE).strftime("%Y-%m-%d")

    print()
    print("PERFECT OUTDOOR WINDOW")
    print(f"Location: {LOCATION_NAME}")
    print(f"Date: {today}")
    print(f"Best outdoor window today: {start:%H:%M}-{end:%H:%M}. "
          f"Average score: {best_window['average_score']:.0f}/100")
    print(
        f"Main reason: {hours['temperature_2m'].mean():.1f} °C on average, "
        f"rain probability up to {hours['precipitation_probability'].max():.0f}%, "
        f"European AQI up to {hours['european_aqi'].max():.0f}"
    )