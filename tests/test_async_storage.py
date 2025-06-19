import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from collector import async_storage

@pytest.mark.asyncio
async def test_async_append_and_query(tmp_path: Path):
    db = tmp_path / "async.db"
    df = pd.DataFrame([
        {"district": "A", "date": "2024-01-01", "temp": 20, "humidity": 50, "wind_speed": 5},
    ])
    await async_storage.append_to_db(df, db)
    out = await async_storage.query_latest(db, limit=1)
    assert len(out) == 1
    assert out.iloc[0]["district"] == "A"

