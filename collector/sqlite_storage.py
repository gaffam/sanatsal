import sqlite3
from pathlib import Path
import pandas as pd

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS weather (
    district TEXT,
    date TEXT,
    temp REAL,
    humidity REAL,
    wind_speed REAL,
    PRIMARY KEY (district, date)
)
"""

INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_weather_date ON weather(date DESC)"


def init_db(db_path: Path) -> None:
    """Initialize SQLite database."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(TABLE_SQL)
        conn.execute(INDEX_SQL)


def append_to_db(df: pd.DataFrame, db_path: Path) -> None:
    """Append dataframe rows to SQLite database."""
    if df.empty:
        return
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        df.to_sql("weather", conn, if_exists="append", index=False)


def query_latest(db_path: Path, limit: int = 100) -> pd.DataFrame:
    """Load latest rows from database ordered by date descending."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        query = (
            "SELECT district, date, temp, humidity, wind_speed "
            "FROM weather ORDER BY date DESC LIMIT ?"
        )
        df = pd.read_sql(query, conn, params=(limit,))
    return df


def query_by_district(db_path: Path, district: str, limit: int = 100) -> pd.DataFrame:
    """Load latest rows for a specific district."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        query = (
            "SELECT district, date, temp, humidity, wind_speed "
            "FROM weather WHERE LOWER(district) = LOWER(?) "
            "ORDER BY date DESC LIMIT ?"
        )
        df = pd.read_sql(query, conn, params=(district, limit))
    return df


def get_statistics(db_path: Path) -> dict:
    """Return simple statistics over the entire dataset."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                AVG(temp) AS avg_temp,
                AVG(humidity) AS avg_humidity,
                AVG(wind_speed) AS avg_wind_speed,
                MAX(temp) AS max_temp,
                MIN(temp) AS min_temp,
                MAX(humidity) AS max_humidity,
                MIN(humidity) AS min_humidity,
                MAX(wind_speed) AS max_wind_speed,
                MIN(wind_speed) AS min_wind_speed
            FROM weather
            """
        ).fetchone()
    keys = [
        "avg_temp",
        "avg_humidity",
        "avg_wind_speed",
        "max_temp",
        "min_temp",
        "max_humidity",
        "min_humidity",
        "max_wind_speed",
        "min_wind_speed",
    ]
    return dict(zip(keys, row))


def query_range(
    db_path: Path,
    start: str | None = None,
    end: str | None = None,
    districts: list[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Return rows within a date range and optional district list."""
    init_db(db_path)
    where = []
    params: list = []
    if start:
        where.append("date >= ?")
        params.append(start)
    if end:
        where.append("date <= ?")
        params.append(end)
    if districts:
        placeholders = ",".join("?" for _ in districts)
        where.append(f"LOWER(district) IN ({placeholders})")
        params.extend(d.lower() for d in districts)
    sql = (
        "SELECT district, date, temp, humidity, wind_speed FROM weather"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY date"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql(sql, conn, params=params)
    return df


def hourly_average(
    db_path: Path,
    start: str | None = None,
    end: str | None = None,
    district: str | None = None,
) -> pd.DataFrame:
    """Return hourly averages of temp/humidity/wind."""
    init_db(db_path)
    where = []
    params: list = []
    if start:
        where.append("date >= ?")
        params.append(start)
    if end:
        where.append("date <= ?")
        params.append(end)
    if district:
        where.append("LOWER(district) = LOWER(?)")
        params.append(district)
    sql = (
        "SELECT substr(date,1,13) as hour, "
        "AVG(temp) as avg_temp, AVG(humidity) as avg_humidity, "
        "AVG(wind_speed) as avg_wind_speed "
        "FROM weather"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY hour ORDER BY hour"
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql(sql, conn, params=params)
    return df
