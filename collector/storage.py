from pathlib import Path
import pandas as pd


def append_json(df: pd.DataFrame, path: Path) -> None:
    """Append weather data to a JSON archive.

    If *path* is a directory, the file ``weather_YYYY_MM.json`` will be
    created inside it so that each month's data is stored separately.
    """
    if path.is_dir() or path.suffix == "":
        path.mkdir(parents=True, exist_ok=True)
        fname = f"weather_{pd.Timestamp.utcnow():%Y_%m}.json"
        path = path / fname
    if path.exists():
        existing = pd.read_json(path)
        df = pd.concat([existing, df], ignore_index=True)
        df = df.drop_duplicates(subset=["district", "date"])
    df.to_json(path, orient="records", force_ascii=False, date_format="iso")


def save_csv(df: pd.DataFrame, path: Path) -> None:
    """Save dataframe as CSV."""
    df.to_csv(path, index=False, encoding="utf-8-sig")
