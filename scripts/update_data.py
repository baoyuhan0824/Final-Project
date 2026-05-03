import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from series_config import SERIES

OUTPUT_PATH = PROJECT_ROOT / "data" / "labor_data.csv"
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


def fetch_bls_data(start_year=2017, end_year=None):
    if end_year is None:
        end_year = datetime.now().year

    payload = {
        "seriesid": list(SERIES.keys()),
        "startyear": str(start_year),
        "endyear": str(end_year),
    }

    api_key = os.getenv("BLS_API_KEY")
    if api_key:
        payload["registrationkey"] = api_key

    response = requests.post(
        BLS_API_URL,
        headers={"Content-type": "application/json"},
        data=json.dumps(payload),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS API request failed: {data}")

    records = []

    for series in data["Results"]["series"]:
        series_id = series["seriesID"]
        info = SERIES.get(series_id, {})

        for item in series["data"]:
            period = item["period"]
            if not period.startswith("M"):
                continue

            year = int(item["year"])
            month = int(period.replace("M", ""))

            raw_value = item.get("value", "").replace(",", "").strip()

            # Skip missing or unavailable values
            if raw_value in ["", "-", "NA", "N/A"]:
                continue

            records.append(
                {
                    "date": pd.Timestamp(year=year, month=month, day=1),
                    "series_id": series_id,
                    "indicator": info.get("name", series_id),
                    "category": info.get("category", "Other"),
                    "unit": info.get("unit", ""),
                    "value": float(raw_value),
                }
            )

    df = pd.DataFrame(records)
    if df.empty:
        raise RuntimeError("No data was returned from the BLS API.")

    df = df.sort_values(["indicator", "date"])
    return df


def add_change_columns(df):
    df = df.copy()
    df["monthly_change"] = df.groupby("indicator")["value"].diff()
    df["year_over_year_change"] = df.groupby("indicator")["value"].diff(12)
    df["monthly_percent_change"] = df.groupby("indicator")["value"].pct_change() * 100
    df["year_over_year_percent_change"] = df.groupby("indicator")["value"].pct_change(12) * 100
    return df


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = fetch_bls_data(start_year=2017)
    df = add_change_columns(df)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved data to: {OUTPUT_PATH}")
    print(f"Rows: {len(df)}")
    print(f"Latest date: {df['date'].max()}")


if __name__ == "__main__":
    main()
