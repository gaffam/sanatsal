import pandas as pd
import pytest
from risk_analyzer import (
    add_risk_column,
    risk_score,
    train_random_forest,
    tune_random_forest,
    predict_with_model,
    merge_with_modis,
)


def test_risk_score_positive():
    row = pd.Series({"temp": 30, "humidity": 40, "wind_speed": 10})
    score = risk_score(row)
    assert score > 0


def test_risk_score_with_brightness():
    row = pd.Series({"temp": 30, "humidity": 40, "wind_speed": 10, "brightness": 100})
    score = risk_score(row)
    assert score > 0


def test_risk_score_seasonal_regional():
    row = pd.Series({
        "temp": 25,
        "humidity": 60,
        "wind_speed": 5,
        "district": "Antalya",
        "date": "2024-07-01",
    })
    score = risk_score(row)
    assert score > 0


def test_add_risk_column():
    df = pd.DataFrame([
        {"district": "A", "date": "2024-01-01", "temp": 30, "humidity": 40, "wind_speed": 10},
        {"district": "B", "date": "2024-01-02", "temp": 15, "humidity": 80, "wind_speed": 5},
    ])
    out = add_risk_column(df)
    assert "risk" in out.columns
    assert len(out) == 2


def test_add_risk_column_vectorized():
    df = pd.DataFrame([
        {"district": "Antalya", "date": "2024-07-02", "temp": 30, "humidity": 40, "wind_speed": 10},
        {"district": "Izmir", "date": "2024-01-02", "temp": 15, "humidity": 80, "wind_speed": 5},
    ])
    out = add_risk_column(df)
    manual = df.apply(risk_score, axis=1)
    assert out["risk"].tolist() == manual.tolist()


def test_random_forest_prediction():
    df = pd.DataFrame([
        {"temp": 30, "humidity": 40, "wind_speed": 10},
        {"temp": 20, "humidity": 50, "wind_speed": 5},
    ])
    df = add_risk_column(df)
    model = train_random_forest(df)
    preds = predict_with_model(model, df)
    assert len(preds) == len(df)


def test_merge_with_modis():
    weather = pd.DataFrame([
        {"district": "A", "date": "2024-01-01", "temp": 20, "humidity": 50, "wind_speed": 5}
    ])
    modis = pd.DataFrame([
        {"acq_date": "2024-01-01", "brightness": 300},
        {"acq_date": "2024-01-02", "brightness": 400},
    ])
    merged = merge_with_modis(weather, modis)
    assert "brightness" in merged.columns
    assert merged.iloc[0]["brightness"] == 300


def test_tune_random_forest():
    pytest.importorskip("optuna")
    df = pd.DataFrame([
        {"temp": 30, "humidity": 40, "wind_speed": 10},
        {"temp": 20, "humidity": 50, "wind_speed": 5},
    ])
    df = add_risk_column(df)
    model = tune_random_forest(df, n_trials=1)
    preds = predict_with_model(model, df)
    assert len(preds) == len(df)
