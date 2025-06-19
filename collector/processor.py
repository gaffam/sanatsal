import pandas as pd

COLUMN_MAP = {
    "ilce": "district",
    "tarih": "date",
    "sicaklik": "temp",
    "nem": "humidity",
    "ruzgarHiz": "wind_speed",
    "ruzgarYon": "wind_dir",
    "havaDurumu": "condition",
}

EXPECTED = [
    "district",
    "date",
    "temp",
    "humidity",
    "wind_speed",
    "wind_dir",
    "condition",
]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns and ensure expected structure."""
    df = df.rename(columns=COLUMN_MAP)
    for col in EXPECTED:
        if col not in df.columns:
            df[col] = None
    df = df[EXPECTED]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["district", "date"])
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Remove missing or out-of-range values."""
    df = df.dropna(subset=["temp", "humidity", "wind_speed", "date", "district"])
    df = df[df["temp"].between(-50, 60)]
    df = df[df["humidity"].between(0, 100)]
    df = df[df["wind_speed"] >= 0]
    return df
