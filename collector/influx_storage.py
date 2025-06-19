"""InfluxDB storage utilities."""
from __future__ import annotations

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd


def write_to_influx(
    df: pd.DataFrame,
    url: str,
    token: str,
    org: str,
    bucket: str,
) -> None:
    """Write a dataframe to InfluxDB."""
    if df.empty:
        return
    client = InfluxDBClient(url=url, token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    points = [
        Point("weather")
        .tag("district", row["district"])
        .field("temp", row["temp"])
        .field("humidity", row["humidity"])
        .field("wind_speed", row["wind_speed"])
        .time(row["date"])
        for row in df.to_dict("records")
    ]
    write_api.write(bucket=bucket, record=points)
    client.close()
