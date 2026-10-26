# The Perfect Outdoor Window

## Project Overview

The Perfect Outdoor Window is a Python project that identifies the best two-hour period for outdoor activities in Vienna based on weather conditions and air quality.

The program retrieves hourly forecast data from the Open-Meteo APIs, validates and combines the data, assigns scores to each hour, and recommends the two-hour window with the highest average score.

The project also uses GitHub Actions to run the program automatically every day.

## How It Works

The program follows these steps:

1. **Fetch data:** Retrieve hourly weather and air-quality forecasts for Vienna.
2. **Validate API responses:** Check that the API requests were successful and that the expected data is available.
3. **Combine data:** Convert the API responses into pandas DataFrames and combine them using timestamps.
4. **Validate the dataset:** Check data types, duplicate timestamps, plausible values, missing hours, and missing observations.
5. **Calculate scores:** Assign points to temperature, precipitation probability, and air quality.
6. **Find the best window:** Evaluate consecutive two-hour periods and select the one with the highest average score.
7. **Display the recommendation:** Print the recommended time window, average score, and a summary of the relevant weather and air-quality conditions.

## Data Sources

The project uses the following APIs from Open-Meteo:

- **Weather Forecast API:** Provides hourly temperature, precipitation probability, and precipitation data.
- **Air Quality API:** Provides hourly PM2.5, PM10, and European Air Quality Index (AQI) data.

The coordinates are configured for Vienna, Austria.

## Scoring Method

Each hour receives a score based on three components:

| Component                     | Maximum score  |
| Temperature                   | 30 points      |
| Precipitation probability     | 30 points      |
| European Air Quality Index    | 40 points      |
| **Total**                     | **100 points** |

Higher scores indicate more favourable conditions for outdoor activities.

The program evaluates consecutive two-hour windows. The window with the highest average hourly score is selected. If multiple windows have the same average score, the earlier window is preferred.

Windows containing missing scores or non-consecutive hours are excluded.

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── daily_run.yml
├── tests/
│   └── test_scoring.py
├── fetch_data.py
├── main.py
├── output.py
├── requirements.txt
├── scoring.py
├── validate_data.py
└── README.md
```

- `main.py`: Runs the complete workflow.
- `fetch_data.py`: Retrieves and combines API data.
- `validate_data.py`: Validates the combined dataset.
- `scoring.py`: Calculates scores and identifies the best two-hour window.
- `output.py`: Displays the final recommendation.
- `tests/test_scoring.py`: Tests the scoring functions and window-selection logic.
- `.github/workflows/daily_run.yml`: Defines the GitHub Actions workflow.
- `requirements.txt`: Lists the required Python packages.

## Installation

Python 3.14 is used in the GitHub Actions workflow.

Clone the repository and navigate to the project directory:

```bash
git clone <YOUR-REPOSITORY-URL>
cd <YOUR-REPOSITORY-NAME>
```

Install the required packages:

```bash
python3 -m pip install -r requirements.txt
```

## Usage

Run the program locally with:

```bash
python3 main.py
```

The program retrieves the latest available forecasts, validates the data, calculates the scores, and prints the best outdoor time window.

## Testing

The project includes tests for the scoring functions and the best-window selection logic.

Install pytest if necessary:

```bash
python3 -m pip install pytest
```

Run the tests from the project root directory:

```bash
python3 -m pytest
```

## Automation with GitHub Actions

The workflow is defined in `.github/workflows/daily_run.yml`.

It can run in three ways:

- Automatically when changes are pushed to the `main` branch.
- Daily according to the configured schedule.
- Manually through the **Run workflow** button in the GitHub Actions tab.

The workflow checks out the repository, sets up Python, installs the dependencies, and executes `main.py`. The program's output can be inspected in the workflow logs.

## Limitations

The recommendation depends on the available forecast data and the scoring thresholds defined in the code. The result is a rule-based recommendation rather than a guarantee of actual outdoor conditions.