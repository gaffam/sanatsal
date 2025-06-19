from fastapi.testclient import TestClient
import pandas as pd
import importlib

from services import collector_service


def test_collector_service_collect(mocker):
    mocker.patch("services.collector_service.collect_and_save")
    client = TestClient(collector_service.app)
    resp = client.post("/collect")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    collector_service.collect_and_save.assert_called_once()


def test_risk_service(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    from collector import sqlite_storage

    sqlite_storage.init_db(db_path)
    sample = pd.DataFrame([
        {"district": "A", "date": "2024-01-01", "temp": 20, "humidity": 50, "wind_speed": 5}
    ])
    sqlite_storage.append_to_db(sample, db_path)

    monkeypatch.setenv("WEATHER_DB", str(db_path))
    mod = importlib.reload(importlib.import_module("services.risk_service"))
    with TestClient(mod.app) as client:
        resp = client.get("/risk?limit=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["district"] == "A"


def test_risk_service_ml(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    from collector import sqlite_storage
    sqlite_storage.init_db(db_path)
    sample = pd.DataFrame([
        {"district": "A", "date": "2024-01-01", "temp": 20, "humidity": 50, "wind_speed": 5}
    ])
    sqlite_storage.append_to_db(sample, db_path)

    from risk_analyzer import add_risk_column, train_random_forest, save_model
    df = add_risk_column(sample)
    model = train_random_forest(df)
    model_path = tmp_path / "model.joblib"
    save_model(model, model_path)

    monkeypatch.setenv("WEATHER_DB", str(db_path))
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    mod = importlib.reload(importlib.import_module("services.risk_service"))
    with TestClient(mod.app) as client:
        resp = client.get("/risk-ml?limit=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "risk" in data[0]
