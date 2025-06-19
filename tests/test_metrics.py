from fastapi.testclient import TestClient
from collector.mgm_client import fetch_latest_weather
from fastapi_app import app


def test_metrics_endpoint(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{
        "ilce": "Test", "sicaklik": 10, "nem": 50, "ruzgarHiz": 5,
        "ruzgarYon": "K", "havaDurumu": "A\u00e7\u0131k"
    }]
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.get", return_value=mock_response)

    fetch_latest_weather()

    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "weather_fetch_total" in resp.text
