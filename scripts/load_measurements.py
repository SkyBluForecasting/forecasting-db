import io
from datetime import datetime, timedelta, timezone

import boto3
import pandas as pd
import requests

# Config
HISTORICAL_BUCKET = "forecasting-forecasts"
HISTORICAL_PREFIX = "historical/"
LOCAL_TZ = "America/New_York"
MEASUREMENTS_API = "http://localhost:8000/assets/{asset_uuid}/measurements/"
API_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkRQVHIzWWZwUHBwNkNsbFoxc1dwcSJ9.eyJpc3MiOiJodHRwczovL2Rldi16azRqMWxiN2RucndjMHhnLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJQdDNpOTBhVG9ya0tZdzNwTjdJVjZ6U1phRHpab1Q1RUBjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly9mb3JlY2FzdGluZy1hcGkuZm9yZWNhc3RpbmciLCJpYXQiOjE3NjAzNjY2ODEsImV4cCI6MTc2MDQ1MzA4MSwic2NvcGUiOiJyZWFkOmZvcmVjYXN0IiwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiUHQzaTkwYVRvcmtLWXczcE43SVY2elNaYUR6Wm9UNUUifQ.ErzvrU5MpQTQXkKGlcfCyTY7uCQXj3FxvkcYZ1GYaATb6GjgFXwwXXn4lN2oPAMwAVL2c4ro1EVue4Lxvcy-SzUPoNI_AJMX6lRwJNVF8M5g9QVj2UHAmcAvp53QXjdOehqmTQPQSp492hIjT1j9VVO3ulTpn0vprdWaZft0By50jhFo9oFjSb8kuHA-FpkxU7KPdgUBtbpo6t3d-0XU_DTKBgwxJbJluNtSjxrw_vI_5v5dOWDVKfqeluRw_MlhzAiaXpjFR9mMrvtIcuF89fn1MiZwXeSLfhfYxTW8x-xHQTmWrN49TrmrxQh6U8Vn_nXuYpF8pwoZKevFDjcvYQ"

# S3 client
s3 = boto3.client("s3")


def list_historical_csvs():
    """List all CSVs under the historical prefix."""
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=HISTORICAL_BUCKET, Prefix=HISTORICAL_PREFIX):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".csv"):
                keys.append(obj["Key"])
    return keys


def process_csv(key: str) -> pd.DataFrame:
    """Fetch CSV from S3, clean + filter data, and return DataFrame."""
    obj = s3.get_object(Bucket=HISTORICAL_BUCKET, Key=key)
    df = pd.read_csv(io.BytesIO(obj["Body"].read()))

    required_cols = {"datetime", "load", "temp"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing one of required columns {required_cols} in {key}")

    # Parse datetimes
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df = df[df["datetime"].notna()]

    # Convert to local for filtering
    df["datetime_local"] = df["datetime"].dt.tz_convert(LOCAL_TZ)

    # Keep up to day-after-tomorrow (48h lookahead)
    now_utc = datetime.now(timezone.utc)
    day_after_tomorrow = now_utc.date() + timedelta(days=2)
    df = df[df["datetime_local"].dt.date <= day_after_tomorrow]

    # Ensure numeric
    df["load"] = pd.to_numeric(df["load"], errors="coerce")
    df["temp"] = pd.to_numeric(df["temp"], errors="coerce")

    # Convert to UTC for API (Z timestamps)
    df["datetime"] = df["datetime_local"].dt.tz_convert("UTC")
    df = df.drop(columns=["datetime_local"])

    return df


def push_to_api(asset_id: str, df: pd.DataFrame):
    measurements = []
    for _, row in df.iterrows():
        ts = row["datetime"].tz_convert("UTC").isoformat().replace("+00:00", "Z")
        if not pd.isna(row["load"]):
            measurements.append(
                {"metric": "load_kw", "timestamp": ts, "value": row["load"]}
            )
        if not pd.isna(row["temp"]):
            measurements.append(
                {"metric": "temp_c", "timestamp": ts, "value": row["temp"]}
            )

    # Batch send to avoid 500 errors
    CHUNK_SIZE = 5000
    url = MEASUREMENTS_API.format(asset_uuid=asset_id)
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    for i in range(0, len(measurements), CHUNK_SIZE):
        chunk = {"measurements": measurements[i : i + CHUNK_SIZE]}
        resp = requests.post(url, json=chunk, headers=headers)
        resp.raise_for_status()
        print(f"Inserted {len(chunk['measurements'])} measurements for {asset_id}")


def main():
    keys = list_historical_csvs()
    print(f"Found {len(keys)} historical CSVs")

    for key in keys:
        # # Assume filename format: historical/<asset_id>_something.csv
        asset_id = key.split("/")[-1].split("_")[0]
        if asset_id == "M4C":
            df = process_csv(key)
            if df.empty:
                print(f"No new data for {asset_id}, skipping.")
                continue

            push_to_api(asset_id, df)


if __name__ == "__main__":
    main()
