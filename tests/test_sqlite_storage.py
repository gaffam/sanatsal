from pathlib import Path
import pandas as pd
from collector.sqlite_storage import (
    init_db,
    append_to_db,
    query_latest,
    query_by_district,
    get_statistics,
    query_range,
    hourly_average,
)


def test_sqlite_append_and_query(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    df = pd.DataFrame([
        {"district": "A", "date": "2024-01-01", "temp": 20, "humidity": 50, "wind_speed": 5},
        {"district": "B", "date": "2024-01-02", "temp": 22, "humidity": 55, "wind_speed": 6},
    ])
    append_to_db(df, db)
    out = query_latest(db, limit=10)
    assert len(out) == 2
    assert set(out["district"]) == {"A", "B"}


def test_query_by_district(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    df = pd.DataFrame([
        {"district": "A", "date": "2024-01-01", "temp": 20, "humidity": 50, "wind_speed": 5},
        {"district": "B", "date": "2024-01-02", "temp": 22, "humidity": 55, "wind_speed": 6},
    ])
    append_to_db(df, db)
    out = query_by_district(db, "A", limit=5)
    assert len(out) == 1
    assert out.iloc[0]["district"] == "A"


def test_get_statistics(tmp_path):
    db = tmp_path / "stats.db"
    init_db(db)
    df = pd.DataFrame([
        {"district": "A", "date": "2024-01-01", "temp": 10, "humidity": 40, "wind_speed": 3},
        {"district": "B", "date": "2024-01-02", "temp": 20, "humidity": 60, "wind_speed": 7},
    ])
    append_to_db(df, db)
    stats = get_statistics(db)
    assert round(stats["avg_temp"], 1) == 15.0
    assert stats["max_humidity"] == 60

def test_query_range(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    df = pd.DataFrame([
        {"district": "A", "date": "2024-01-01T10:00", "temp": 20, "humidity": 50, "wind_speed": 5},
        {"district": "A", "date": "2024-01-02T10:00", "temp": 22, "humidity": 55, "wind_speed": 6},
    ])
    append_to_db(df, db)
    out = query_range(db, start="2024-01-01", end="2024-01-03", districts=["A"])
    assert len(out) == 2


def test_hourly_average(tmp_path):
    db = tmp_path / "avg.db"
    init_db(db)
    df = pd.DataFrame([
        {"district": "A", "date": "2024-01-01T10:10", "temp": 20, "humidity": 50, "wind_speed": 5},
        {"district": "A", "date": "2024-01-01T10:40", "temp": 22, "humidity": 60, "wind_speed": 7},
    ])
    append_to_db(df, db)
    out = hourly_average(db, district="A")
    assert len(out) == 1
    assert round(out.iloc[0]["avg_temp"], 1) == 21.0
