import aiosqlite
import pandas as pd
from pathlib import Path

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

async def init_db(db_path: Path) -> None:
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(TABLE_SQL)
        await conn.commit()

async def append_to_db(df: pd.DataFrame, db_path: Path) -> None:
    if df.empty:
        return
    await init_db(db_path)
    records = df[["district", "date", "temp", "humidity", "wind_speed"]].to_records(index=False)
    async with aiosqlite.connect(db_path) as conn:
        await conn.executemany(
            "INSERT OR REPLACE INTO weather (district, date, temp, humidity, wind_speed) VALUES (?,?,?,?,?)",
            list(records),
        )
        await conn.commit()

async def query_latest(db_path: Path, limit: int = 100) -> pd.DataFrame:
    await init_db(db_path)
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT district, date, temp, humidity, wind_speed FROM weather ORDER BY date DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        cols = [c[0] for c in cursor.description]
    return pd.DataFrame(rows, columns=cols)

async def query_by_district(db_path: Path, district: str, limit: int = 100) -> pd.DataFrame:
    await init_db(db_path)
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT district, date, temp, humidity, wind_speed FROM weather WHERE LOWER(district)=LOWER(?) ORDER BY date DESC LIMIT ?",
            (district, limit),
        )
        rows = await cursor.fetchall()
        cols = [c[0] for c in cursor.description]
    return pd.DataFrame(rows, columns=cols)

async def get_statistics(db_path: Path) -> dict:
    await init_db(db_path)
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            """
            SELECT
                AVG(temp) as avg_temp,
                AVG(humidity) as avg_humidity,
                AVG(wind_speed) as avg_wind_speed,
                MAX(temp) as max_temp,
                MIN(temp) as min_temp,
                MAX(humidity) as max_humidity,
                MIN(humidity) as min_humidity,
                MAX(wind_speed) as max_wind_speed,
                MIN(wind_speed) as min_wind_speed
            FROM weather
            """
        )
        row = await cursor.fetchone()
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

async def query_range(
    db_path: Path,
    start: str | None = None,
    end: str | None = None,
    districts: list[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    await init_db(db_path)
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
    sql = "SELECT district, date, temp, humidity, wind_speed FROM weather"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY date"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        cols = [c[0] for c in cursor.description]
    return pd.DataFrame(rows, columns=cols)

async def hourly_average(
    db_path: Path,
    start: str | None = None,
    end: str | None = None,
    district: str | None = None,
) -> pd.DataFrame:
    await init_db(db_path)
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
        "SELECT substr(date,1,13) as hour, AVG(temp) as avg_temp, AVG(humidity) as avg_humidity, "
        "AVG(wind_speed) as avg_wind_speed FROM weather"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY hour ORDER BY hour"
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        cols = [c[0] for c in cursor.description]
    return pd.DataFrame(rows, columns=cols)
