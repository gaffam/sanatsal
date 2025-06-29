import pandas as pd
from pathlib import Path
from data_collector import collect_and_save


def test_collect_and_save(tmp_path, mocker):
    sample = pd.DataFrame([
        {
            "district": "A",
            "date": "2024-01-01",
            "temp": 20,
            "humidity": 50,
            "wind_speed": 5,
            "wind_dir": "K",
            "condition": "Açık",
        }
    ])
    mocker.patch("data_collector.fetch_latest_weather", return_value=sample)
    json_dir = tmp_path / "out"
    collect_and_save(json_dir)
    files = list(json_dir.glob("*.json"))
    assert files, "monthly file not created"
    out = pd.read_json(files[0])
    assert list(out.columns) == [
        "district",
        "date",
        "temp",
        "humidity",
        "wind_speed",
        "wind_dir",
        "condition",
    ]
    assert len(out) == 1
    assert out.iloc[0]["district"] == "A"

def test_collect_s3_upload(tmp_path, mocker):
    df = pd.DataFrame([
        {
            "district": "B",
            "date": "2024-01-02",
            "temp": 21,
            "humidity": 40,
            "wind_speed": 3,
        }
    ])
    mocker.patch("data_collector.fetch_latest_weather", return_value=df)
    upload_mock = mocker.patch("data_collector.upload_file")
    out = tmp_path / "file.json"
    collect_and_save(out, s3_bucket="bucket", s3_key="k")
    upload_mock.assert_called_once()

