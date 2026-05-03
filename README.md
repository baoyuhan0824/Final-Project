# U.S. Labor Statistics Dashboard

This project is a Streamlit dashboard that displays selected monthly labor market indicators from the U.S. Bureau of Labor Statistics.

## Indicators

The dashboard includes:

- Total nonfarm employment
- Unemployment rate
- Civilian labor force
- Civilian employment
- Civilian unemployment
- Average hourly earnings
- Average weekly hours

## How to run locally

Install the required packages:

```bash
pip install -r requirements.txt
```

Download and prepare the data:

```bash
python scripts/update_data.py
```

Run the dashboard:

```bash
streamlit run app.py
```

## Automation

The project includes a GitHub Actions workflow that runs once per month. It downloads the newest BLS data, cleans it, updates the CSV file, and commits the updated dataset back to the repository.

## Data source

U.S. Bureau of Labor Statistics Public Data API.
