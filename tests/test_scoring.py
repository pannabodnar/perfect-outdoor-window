import math

import pandas as pd

from scoring import (
    temperature_score, rain_score, air_quality_score, add_scores,
    find_best_window, NoValidWindowError,
)

def test_temperature_score():
    assert temperature_score(20) == 30      # ideal
    assert temperature_score(15) == 30      # lower boundary of the best range
    assert temperature_score(25) == 30      # upper boundary of the best range
    assert temperature_score(14.9) == 20
    assert temperature_score(10) == 20
    assert temperature_score(25.1) == 20
    assert temperature_score(30) == 20
    assert temperature_score(9.9) == 0
    assert temperature_score(30.1) == 0
    assert temperature_score(-5) == 0


def test_rain_score():
    assert rain_score(0) == 30
    assert rain_score(10) == 30
    assert rain_score(10.1) == 20
    assert rain_score(30) == 20
    assert rain_score(30.1) == 10
    assert rain_score(60) == 10
    assert rain_score(60.1) == 0
    assert rain_score(100) == 0


def test_air_quality_score():
    assert air_quality_score(0) == 40
    assert air_quality_score(20) == 40
    assert air_quality_score(20.1) == 30
    assert air_quality_score(40) == 30
    assert air_quality_score(40.1) == 15
    assert air_quality_score(60) == 15
    assert air_quality_score(60.1) == 5
    assert air_quality_score(80) == 5
    assert air_quality_score(80.1) == 0

# check that missing data is not treated as a score of zero.
def test_missing_values_are_not_zero():
    # Check that if the temperature is missing, the temperature-scoring function also returns a missing value.
    assert math.isnan(temperature_score(float("nan")))
    assert math.isnan(rain_score(float("nan")))
    assert math.isnan(air_quality_score(float("nan")))

# check whether  add_scores() function correctly calculates the total score for each hour
def test_add_scores_matches_the_pdf_example():
    df = pd.DataFrame({
        "temperature_2m": [18, 20, 22, 20],
        "precipitation_probability": [10, 10, 25, 10],
        "european_aqi": [18, 22, 35, float("nan")],
        "data_status": ["complete", "complete", "complete", "incomplete"],
    })

    # This calls the add_scores() function from scoring.py. 
    # It calculates the individual scores and adds a total_score column.
    result = add_scores(df)

    assert result.loc[0, "total_score"] == 100   # 30 + 30 + 40
    assert result.loc[1, "total_score"] == 90    # 30 + 30 + 30
    assert result.loc[2, "total_score"] == 80    # 30 + 20 + 30
    assert math.isnan(result.loc[3, "total_score"])  # incomplete hour: no score

# A shortcut for creating test data. 
# It does not calculate any scores; it simply puts the times and scores into a table
def make_scores(times, scores):
    return pd.DataFrame({"time": pd.to_datetime(times), "total_score": scores})


def test_best_window_matches_the_pdf_example():
    df = make_scores(
        # Create the test data
        ["2026-10-24 09:00", "2026-10-24 10:00", "2026-10-24 11:00", "2026-10-24 12:00"],
        [100, 90, 80, 95],
    )
    # Define the analysis period
    start = pd.Timestamp("2026-10-24 09:00")
    end = pd.Timestamp("2026-10-24 13:00")

    # Find the best window
    best, windows = find_best_window(df, start, end)

    assert best["window_start"] == pd.Timestamp("2026-10-24 09:00")
    assert best["window_end"] == pd.Timestamp("2026-10-24 11:00")
    assert best["average_score"] == 95
    assert list(windows["average_score"]) == [95, 87.5, 85]


def test_tie_selects_the_earlier_window():
    df = make_scores(
        ["2026-10-24 09:00", "2026-10-24 10:00", "2026-10-24 11:00"],
        [80, 80, 80],
    )
    # best receives the best window
    # _ receives the list of all windows, but we don't need it in this test
    # Using _ is a common Python convention meaning: I don't need this value
    best, _ = find_best_window(
        df, pd.Timestamp("2026-10-24 09:00"), pd.Timestamp("2026-10-24 12:00")
    )
    # This checks whether the selected window starts at 09:00
    assert best["window_start"] == pd.Timestamp("2026-10-24 09:00")


def test_windows_with_missing_scores_are_skipped():
    df = make_scores(
        ["2026-10-24 09:00", "2026-10-24 10:00", "2026-10-24 11:00", "2026-10-24 12:00"],
        [100, float("nan"), 90, 90],
    )
    best, windows = find_best_window(
        df, pd.Timestamp("2026-10-24 09:00"), pd.Timestamp("2026-10-24 13:00")
    )
    assert len(windows) == 1
    assert best["window_start"] == pd.Timestamp("2026-10-24 11:00")


def test_windows_with_a_missing_hour_are_skipped():
    # the 10:00 row is missing, so 09:00 and 11:00 are not consecutive
    df = make_scores(
        ["2026-10-24 09:00", "2026-10-24 11:00", "2026-10-24 12:00"],
        [100, 80, 80],
    )
    best, windows = find_best_window(
        df, pd.Timestamp("2026-10-24 09:00"), pd.Timestamp("2026-10-24 13:00")
    )
    assert len(windows) == 1
    assert best["window_start"] == pd.Timestamp("2026-10-24 11:00")


def test_no_valid_window_raises_an_error():
    df = make_scores(
        ["2026-10-24 09:00", "2026-10-24 10:00", "2026-10-24 11:00", "2026-10-24 12:00"],
        [float("nan"), 50, float("nan"), 50],
    )
    try:
        find_best_window(
            df, pd.Timestamp("2026-10-24 09:00"), pd.Timestamp("2026-10-24 13:00")
        )
        #This line is reached only if find_best_window() does not raise an error.
        # assert False deliberately fails the test.
        # "NoValidWindowError was expected" explains why it failed.
        assert False, "NoValidWindowError was expected"
    except NoValidWindowError:
        # pass means "do nothing." The error was expected, so the test can finish successfully.
        pass