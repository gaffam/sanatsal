import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from collector.processor import normalize, clean


def test_normalize_renames_columns():
    raw_df = pd.DataFrame([
        {
            "ilce": "Test_Ilce",
            "tarih": "2025-06-19T10:00:00.000Z",
            "sicaklik": 25,
            "nem": 60,
            "ruzgarHiz": 15,
            "ruzgarYon": "K",
            "havaDurumu": "Açık",
        }
    ])
    normalized_df = normalize(raw_df)
    expected_columns = [
        "district",
        "date",
        "temp",
        "humidity",
        "wind_speed",
        "wind_dir",
        "condition",
    ]
    assert list(normalized_df.columns) == expected_columns
    assert normalized_df.iloc[0]["district"] == "Test_Ilce"


def test_clean_removes_out_of_range_temp():
    df = pd.DataFrame([
        {"temp": 25, "humidity": 50, "wind_speed": 10, "date": "2025-06-19", "district": "A"},
        {"temp": 99, "humidity": 50, "wind_speed": 10, "date": "2025-06-19", "district": "B"},
    ])
    cleaned_df = clean(df)
    assert len(cleaned_df) == 1
    assert cleaned_df.iloc[0]["temp"] == 25
