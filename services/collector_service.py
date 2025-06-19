from fastapi import FastAPI
from pathlib import Path
import os

from data_collector import collect_and_save

app = FastAPI(title="Collector Service")

JSON_OUTPUT = Path(os.getenv("JSON_OUTPUT", "weather_data.json"))
CSV_OUTPUT = os.getenv("CSV_OUTPUT")
DB_OUTPUT = os.getenv("WEATHER_DB")

@app.post("/collect")
async def collect(district: str | None = None):
    csv_path = Path(CSV_OUTPUT) if CSV_OUTPUT else None
    db_path = Path(DB_OUTPUT) if DB_OUTPUT else None
    collect_and_save(JSON_OUTPUT, csv_output=csv_path, db_output=db_path, district=district)
    return {"status": "ok"}

