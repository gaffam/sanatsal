from fastapi import FastAPI
from pathlib import Path
import os
from typing import List

from collector import sqlite_storage, timescale_storage
from risk_analyzer import add_risk_column, load_model, predict_with_model
from fastapi_app import WeatherRecord
from pydantic import BaseModel


async def lifespan(app: FastAPI):
    global _model
    if MODEL_PATH.exists():
        _model = load_model(str(MODEL_PATH))
    yield

app = FastAPI(title="Risk Service", lifespan=lifespan)
DB_PATH = Path(os.getenv("WEATHER_DB", "weather.db"))
DB_URL = os.getenv("TIMESCALE_URL")
MODEL_PATH = Path(os.getenv("MODEL_PATH", "models/model.joblib"))
_model = None


class WeatherRecordWithRisk(WeatherRecord):
    risk: float


@app.get("/risk", response_model=List[WeatherRecord])
async def risk(limit: int = 100):
    if DB_URL:
        df = timescale_storage.query_range_ts(DB_URL, limit=limit)
    else:
        df = sqlite_storage.query_latest(DB_PATH, limit)
    df = add_risk_column(df)
    return df.to_dict(orient="records")


@app.get("/risk-ml", response_model=List[WeatherRecordWithRisk])
async def risk_ml(limit: int = 100):
    if _model is None:
        raise RuntimeError("Model not loaded")
    if DB_URL:
        df = timescale_storage.query_range_ts(DB_URL, limit=limit)
    else:
        df = sqlite_storage.query_latest(DB_PATH, limit)
    preds = predict_with_model(_model, df)
    df = df.assign(risk=preds)
    return df.to_dict(orient="records")
