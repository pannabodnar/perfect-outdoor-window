import math

import pandas as pd

from scoring import temperature_score, rain_score, air_quality_score, add_scores


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


def test_missing_values_are_not_zero():
    assert math.isnan(temperature_score(float("nan")))
    assert math.isnan(rain_score(float("nan")))
    assert math.isnan(air_quality_score(float("nan")))


def test_add_scores_matches_the_pdf_example():
    df = pd.DataFrame({
        "temperature_2m": [18, 20, 22, 20],
        "precipitation_probability": [10, 10, 25, 10],
        "european_aqi": [18, 22, 35, float("nan")],
        "data_status": ["complete", "complete", "complete", "incomplete"],
    })
    result = add_scores(df)

    assert result.loc[0, "total_score"] == 100   # 30 + 30 + 40
    assert result.loc[1, "total_score"] == 90    # 30 + 30 + 30
    assert result.loc[2, "total_score"] == 80    # 30 + 20 + 30
    assert math.isnan(result.loc[3, "total_score"])  # incomplete hour: no score