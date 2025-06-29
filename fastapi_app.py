from pathlib import Path
import os
from typing import List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
import structlog
import asyncio

ASYNC = os.getenv("ASYNC_DB", "0") == "1"

if ASYNC:
    from collector import async_storage as storage
else:
    from collector import sqlite_storage as storage
from collector.middlewares import RateLimitMiddleware
from collector.logging_config import setup_logging
from risk_analyzer import add_risk_column

DB_PATH = Path(os.getenv("WEATHER_DB", "weather.db"))
API_KEY = os.getenv("API_KEY")

async def require_api_key(x_api_key: str = Header(default="")):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

setup_logging()
logger = structlog.get_logger(__name__)

async def lifespan(app: FastAPI):
    if ASYNC:
        await storage.init_db(DB_PATH)
    else:
        await asyncio.to_thread(storage.init_db, DB_PATH)
    yield

app = FastAPI(title="Banksia API", lifespan=lifespan)

redis_url = os.getenv("REDIS_URL")
app.add_middleware(RateLimitMiddleware, max_requests=100, window=60, redis_url=redis_url)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
app.add_middleware(HTTPSRedirectMiddleware)

# expose Prometheus metrics at /metrics
Instrumentator().instrument(app).expose(app)

# serve the Vue dashboard
app.mount(
    "/dashboard",
    StaticFiles(directory="frontend", html=True),
    name="dashboard",
)


class WeatherRecord(BaseModel):
    district: str
    date: str
    temp: float
    humidity: float
    wind_speed: float


@app.get("/api/latest-data", response_model=List[WeatherRecord])
async def latest_data(limit: int = 100, _=Depends(require_api_key)):
    try:
        if ASYNC:
            df = await storage.query_latest(DB_PATH, limit)
        else:
            df = await asyncio.to_thread(storage.query_latest, DB_PATH, limit)
    except Exception as exc:
        logger.error("query_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    return df.to_dict(orient="records")


@app.get("/api/by-district", response_model=List[WeatherRecord])
async def by_district(name: str, limit: int = 100, _=Depends(require_api_key)):
    try:
        if ASYNC:
            df = await storage.query_by_district(DB_PATH, name, limit)
        else:
            df = await asyncio.to_thread(storage.query_by_district, DB_PATH, name, limit)
    except Exception as exc:
        logger.error("query_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    return df.to_dict(orient="records")


class Stats(BaseModel):
    avg_temp: float | None
    avg_humidity: float | None
    avg_wind_speed: float | None
    max_temp: float | None
    min_temp: float | None
    max_humidity: float | None
    min_humidity: float | None
    max_wind_speed: float | None
    min_wind_speed: float | None


@app.get("/api/statistics", response_model=Stats)
async def statistics(_=Depends(require_api_key)):
    try:
        if ASYNC:
            stats = await storage.get_statistics(DB_PATH)
        else:
            stats = await asyncio.to_thread(storage.get_statistics, DB_PATH)
    except Exception as exc:
        logger.error("stats_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    return stats

class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.remove(websocket)

    async def broadcast(self, message: str) -> None:
        for ws in list(self.active):
            try:
                await ws.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(ws)

manager = ConnectionManager()

@app.websocket("/ws/weather")
async def websocket_weather(ws: WebSocket, api_key: str = Header(default="")):
    if API_KEY and api_key != API_KEY:
        await ws.close(code=1008)
        return
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
            if ASYNC:
                df = await storage.query_latest(DB_PATH, limit=1)
            else:
                df = await asyncio.to_thread(storage.query_latest, DB_PATH, 1)
            await manager.broadcast(df.to_json(orient="records"))
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/api/data-range", response_model=List[WeatherRecord])
async def data_range(
    start: str | None = None,
    end: str | None = None,
    districts: str | None = None,
    limit: int | None = None,
    _=Depends(require_api_key),
):
    try:
        dlist = districts.split(",") if districts else None
        if ASYNC:
            df = await storage.query_range(DB_PATH, start=start, end=end, districts=dlist, limit=limit)
        else:
            df = await asyncio.to_thread(storage.query_range, DB_PATH, start, end, dlist, limit)
    except Exception as exc:
        logger.error("range_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    return df.to_dict(orient="records")


@app.get("/api/hourly-average")
async def hourly_avg(
    start: str | None = None,
    end: str | None = None,
    district: str | None = None,
    _=Depends(require_api_key),
):
    try:
        if ASYNC:
            df = await storage.hourly_average(DB_PATH, start=start, end=end, district=district)
        else:
            df = await asyncio.to_thread(storage.hourly_average, DB_PATH, start, end, district)
    except Exception as exc:
        logger.error("avg_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    return df.to_dict(orient="records")


@app.get("/api/risk-score")
async def risk_score_endpoint(limit: int = 100, _=Depends(require_api_key)):
    try:
        if ASYNC:
            df = await storage.query_latest(DB_PATH, limit)
        else:
            df = await asyncio.to_thread(storage.query_latest, DB_PATH, limit)
        df = add_risk_column(df)
    except Exception as exc:
        logger.error("risk_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    return df.to_dict(orient="records")
