from __future__ import annotations

"""PostgreSQL storage utilities using SQLAlchemy."""

from typing import Iterable
from sqlalchemy import create_engine, text
import pandas as pd

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS weather (
    district TEXT,
    date TIMESTAMP,
    temp REAL,
    humidity REAL,
    wind_speed REAL,
    PRIMARY KEY (district, date)
)
"""


def init_pg(db_url: str) -> None:
    """Ensure the weather table exists."""
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text(TABLE_SQL))


def append_to_pg(df: pd.DataFrame, db_url: str) -> None:
    """Append dataframe to PostgreSQL."""
    if df.empty:
        return
    engine = create_engine(db_url)
    with engine.begin() as conn:
        df.to_sql("weather", conn, if_exists="append", index=False)


def query_range_pg(
    db_url: str,
    start: str | None = None,
    end: str | None = None,
    districts: Iterable[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Query data from PostgreSQL within an optional time range and district list."""
    engine = create_engine(db_url)
    where = []
    params = {}
    if start:
        where.append("date >= :start")
        params["start"] = start
    if end:
        where.append("date <= :end")
        params["end"] = end
    if districts:
        where.append("lower(district) IN :dlist")
        params["dlist"] = tuple(d.lower() for d in districts)
    sql = "SELECT district, date, temp, humidity, wind_speed FROM weather"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY date"
    if limit:
        sql += " LIMIT :limit"
        params["limit"] = limit
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params=params)
    return df
