import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from collector.mgm_client import fetch_latest_weather

def test_fetch_latest_weather_success(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{
        "ilce": "Test",
        "sicaklik": 10,
        "nem": 50,
        "ruzgarHiz": 5,
        "ruzgarYon": "K",
        "havaDurumu": "Açık",
    }]
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_response)

    df = fetch_latest_weather()
    assert not df.empty
    assert df.iloc[0]["ilce"] == "Test"
