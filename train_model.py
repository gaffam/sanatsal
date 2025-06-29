import os
import pandas as pd
from pathlib import Path
from collector import sqlite_storage, timescale_storage
from risk_analyzer import (
    train_random_forest,
    tune_random_forest,
    save_model,
    add_risk_column,
)

DB_PATH = Path(os.getenv("WEATHER_DB", "weather.db"))
DB_URL = os.getenv("TIMESCALE_URL")
MODEL_PATH = Path("models/model.joblib")

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Train risk prediction model")
    parser.add_argument("--tune", action="store_true", help="Use Optuna tuning")
    parser.add_argument("--trials", type=int, default=20, help="Number of Optuna trials")
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Number of rows to fetch for training (0 for all)",
    )
    args = parser.parse_args()

    limit = None if args.limit == 0 else args.limit

    if DB_URL:
        df = timescale_storage.query_range_ts(DB_URL, limit=limit)
    else:
        sqlite_storage.init_db(DB_PATH)
        df = sqlite_storage.query_latest(DB_PATH, limit=limit)

    df = add_risk_column(df)
    if args.tune:
        model = tune_random_forest(df, n_trials=args.trials)
    else:
        model = train_random_forest(df)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    save_model(model, MODEL_PATH)

if __name__ == "__main__":
    main()
