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
# MEASUREMENTS_API = "http://18.220.250.165/assets/{asset_uuid}/measurements/"
API_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IkRQVHIzWWZwUHBwNkNsbFoxc1dwcSJ9.eyJpc3MiOiJodHRwczovL2Rldi16azRqMWxiN2RucndjMHhnLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJQdDNpOTBhVG9ya0tZdzNwTjdJVjZ6U1phRHpab1Q1RUBjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly9mb3JlY2FzdGluZy1hcGkuZm9yZWNhc3RpbmciLCJpYXQiOjE3NjI2MTgzNTgsImV4cCI6MTc2MjcwNDc1OCwic2NvcGUiOiJyZWFkOmZvcmVjYXN0IiwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiUHQzaTkwYVRvcmtLWXczcE43SVY2elNaYUR6Wm9UNUUifQ.SPy2eGGperA6f-WDeT8v1vl9YS7Jvr56F-wxu-MyCuHTuU-unGP9ja9mGEbCWmB-oFJehYiRDoG6TraK0GbpOM51V6fewGCn7jD-c9rS22fHnCLYVe4CoWhqQXZL_KfZuMY2c5yiFvqx_hMYrMbeZ-TxvSrkpRPcScNa75jU_OOP3SfeN9OzWTKaPWN5oR7bsug-qbe1WLiOE3ytYzOs8Gjhj7d9I_qQpvUIsbJkrzFkzpVwVRFEN7TXyuC3NWIfNIfe7KLP4G3Itg_gIe20PAb9b0ZW2C56tiLmbDkd88MZNBXXRMaoiILwhATRpe_SSbaoE9B_2dw2EiFWxod_pA"
s3 = boto3.client("s3")


def list_historical_csvs():
    """List all CSV keys in the historical S3 prefix."""
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=HISTORICAL_BUCKET, Prefix=HISTORICAL_PREFIX):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".csv"):
                keys.append(obj["Key"])
    return keys


def load_and_clean_csv(key: str) -> pd.DataFrame:
    """Load CSV from S3, parse datetime, filter up to 48h look-ahead, mark load NaN for look-ahead."""
    obj = s3.get_object(Bucket=HISTORICAL_BUCKET, Key=key)
    df = pd.read_csv(io.BytesIO(obj["Body"].read()))

    if "datetime" not in df.columns:
        raise ValueError(f"'datetime' column missing in {key}")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df = df[df["datetime"].notna()]

    df["datetime_local"] = df["datetime"].dt.tz_convert(LOCAL_TZ)

    now_utc = datetime.now(timezone.utc)

    # Keep rows up to 48h look-ahead
    future_cutoff = now_utc + timedelta(hours=48)
    df = df[(df["datetime"] <= future_cutoff)]

    # Future load values are ignored (not pushed)
    df["load"] = df["load"].where(df["datetime"] <= now_utc, float("nan"))

    # Ensure temp is numeric
    df["temp"] = pd.to_numeric(df["temp"], errors="coerce")

    # Convert back to UTC for API
    df["datetime"] = df["datetime_local"].dt.tz_convert("UTC")
    df = df.drop(columns=["datetime_local"])

    return df


def fetch_existing_measurements(
    asset_id: str, start_time: datetime, end_time: datetime
) -> dict:
    """Get measurements already in the DB for this asset and time range."""
    url = MEASUREMENTS_API.format(asset_uuid=asset_id)
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    params = {"start_time": start_time.isoformat(), "end_time": end_time.isoformat()}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def identify_new_measurements(df: pd.DataFrame, existing: dict):
    """Return only measurements missing in DB, respecting look-ahead rules."""
    # Existing set keyed by (timestamp_iso, metric)
    existing_dict = {
        (row["timestamp"], metric): row["values"].get(metric)
        for row in existing["values"]
        for metric in row["values"]
    }

    new_measurements = []
    for _, row in df.iterrows():
        ts = row["datetime"].isoformat().replace("+00:00", "Z")
        for metric in ["load", "temp"]:
            value = row[metric]
            if pd.isna(value):
                continue

            # Track if missing in DB or if DB value is NaN
            if (ts, metric) not in existing_dict or pd.isna(
                existing_dict[(ts, metric)]
            ):
                new_measurements.append(
                    {"metric": metric, "timestamp": ts, "value": value}
                )

    return new_measurements


def upload_measurements(asset_id: str, measurements: list, chunk_size: int = 500):
    """Upload measurements safely in chunks to avoid parameter limit errors."""
    if not measurements:
        print(f"No new measurements to upload for {asset_id}.")
        return

    url = MEASUREMENTS_API.format(asset_uuid=asset_id)
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    total = len(measurements)
    print(f"Uploading {total} measurements for {asset_id} in chunks of {chunk_size}...")

    for i in range(0, total, chunk_size):
        chunk = {"measurements": measurements[i : i + chunk_size]}
        resp = requests.post(url, json=chunk, headers=headers)
        resp.raise_for_status()
        print(
            f"  Inserted {len(chunk['measurements'])} measurements (chunk {i // chunk_size + 1})"
        )


def process_asset_csv(key: str):
    asset_id = key.split("/")[-1].split("_")[0]
    if asset_id == "M9A":
        df = load_and_clean_csv(key)
        if df.empty:
            print(f"No measurements to process for {asset_id}.")
            return

        existing = fetch_existing_measurements(
            asset_id, df["datetime"].min(), df["datetime"].max()
        )
        new_measurements = identify_new_measurements(df, existing)
        upload_measurements(asset_id, new_measurements, chunk_size=500)


def main():
    keys = list_historical_csvs()
    print(f"Found {len(keys)} historical CSVs.")

    for key in keys:
        process_asset_csv(key)


if __name__ == "__main__":
    main()
