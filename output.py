import pandas as pd

from fetch_data import TIMEZONE

LOCATION_NAME = "Vienna"


def print_recommendation(best_window, hourly_df):
    """Print the final recommendation and the main reason for it."""
    start = best_window["window_start"]
    end = best_window["window_end"]

    # Hours that belong to the recommended window
    # hourly_df[...] selects the rows that satisfy both conditions.
    # hours = stores the filtered DataFrame in a new variable called hours.
    # For example, if the recommended window is 15:00–17:00, hours contains the observations for 15:00 and 16:00.
    hours = hourly_df[(hourly_df["time"] >= start) & (hourly_df["time"] < end)]

    # Get today's date
    # pd.Timestamp.now() gets the current date and time.
    # tz=TIMEZONE specifies the timezone imported from fetch_data.py.
    # .strftime("%Y-%m-%d") formats the date as year-month-day.
    today = pd.Timestamp.now(tz=TIMEZONE).strftime("%Y-%m-%d")

    # Print the recommendation
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