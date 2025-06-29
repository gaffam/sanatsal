"""Fire risk analysis utilities with ML support."""
from __future__ import annotations


from typing import Any


from typing import Any
main
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, cross_val_score
import joblib


# simple lookup tables for seasonal and regional adjustments
SEASON_FACTORS = {6: 0.2, 7: 0.2, 8: 0.2, 12: -0.1, 1: -0.1, 2: -0.1}
REGIONAL_FACTORS = {
    "antalya": 0.3,
    "muğla": 0.2,
    "mugla": 0.2,
}


def risk_score(row: pd.Series) -> float:
    """Calculate a risk score with seasonal and regional adjustments."""


def risk_score(row: pd.Series) -> float:
    """Calculate a basic risk score including optional satellite brightness."""
 main
    temp_score = (row["temp"] - 20) * 0.3
    wind_score = row["wind_speed"] * 0.3
    humidity_score = (100 - row["humidity"]) * 0.2
    brightness_score = row.get("brightness", 0) * 0.05

    month_val = pd.to_datetime(row.get("date"), errors="coerce")
    month = month_val.month if not pd.isna(month_val) else None
    season = SEASON_FACTORS.get(month, 0)
    region = REGIONAL_FACTORS.get(str(row.get("district", "")).lower(), 0)

    score = temp_score + wind_score + humidity_score + brightness_score
    score += season + region
    return max(score, 0.0)

    return max(temp_score + wind_score + humidity_score + brightness_score, 0.0)
main


def add_risk_column(df: pd.DataFrame) -> pd.DataFrame:
    """Return a new dataframe with a calculated risk column."""
    df = df.copy()

    brightness = df["brightness"] if "brightness" in df.columns else 0
    temp_score = (df["temp"] - 20) * 0.3
    wind_score = df["wind_speed"] * 0.3
    humidity_score = (100 - df["humidity"]) * 0.2

    if "date" in df.columns:
        months = pd.to_datetime(df["date"], errors="coerce").dt.month
    else:
        months = pd.Series([None] * len(df))
    season = months.map(SEASON_FACTORS).fillna(0)
    if "district" in df.columns:
        region = df["district"].str.lower().map(REGIONAL_FACTORS).fillna(0)
    else:
        region = 0

    df["risk"] = (
        temp_score + wind_score + humidity_score + brightness * 0.05 + season + region
    ).clip(lower=0)

    df["risk"] = df.apply(risk_score, axis=1)
 main
    return df


def merge_with_modis(weather_df: pd.DataFrame, modis_df: pd.DataFrame) -> pd.DataFrame:
    """Merge aggregated MODIS brightness with weather data."""
    m = modis_df.copy()
    m["date"] = pd.to_datetime(m.get("acq_date"), errors="coerce").dt.date.astype(str)
    daily = m.groupby("date")[["brightness"]].mean().reset_index()
    w = weather_df.copy()
    w["date_only"] = pd.to_datetime(w["date"], errors="coerce").dt.date.astype(str)
    merged = w.merge(daily, left_on="date_only", right_on="date", how="left")
    merged["brightness"] = merged["brightness"].fillna(0)
    merged = merged.drop(columns=["date_y", "date_only"], errors="ignore").rename(columns={"date_x": "date"})
    return merged


def train_random_forest(df: pd.DataFrame, target: str = "risk") -> RandomForestRegressor:
    """Train a RandomForest model for risk prediction."""
    cols = ["temp", "humidity", "wind_speed"]
    if "brightness" in df.columns:
        cols.append("brightness")
    features = df[cols]
    y = df[target]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(features, y)
    return model


def train_random_forest_grid(df: pd.DataFrame, target: str = "risk") -> RandomForestRegressor:
    """Train a RandomForest with hyperparameter search."""
    cols = ["temp", "humidity", "wind_speed"]
    if "brightness" in df.columns:
        cols.append("brightness")
    X, y = df[cols], df[target]
    params = {"n_estimators": [50, 100], "max_depth": [None, 10, 20]}
    grid = GridSearchCV(RandomForestRegressor(random_state=42), params, cv=3)
    grid.fit(X, y)
    return grid.best_estimator_


def tune_random_forest(df: pd.DataFrame, target: str = "risk", n_trials: int = 20) -> RandomForestRegressor:
    """Tune a RandomForest using Optuna for better hyperparameters."""
    try:
        import optuna
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("optuna is not installed") from exc

    cols = ["temp", "humidity", "wind_speed"]
    if "brightness" in df.columns:
        cols.append("brightness")
    X, y = df[cols], df[target]

    def objective(trial: optuna.Trial) -> float:
        model = RandomForestRegressor(
            n_estimators=trial.suggest_int("n_estimators", 50, 200),
            max_depth=trial.suggest_int("max_depth", 2, 20),
            min_samples_split=trial.suggest_int("min_samples_split", 2, 10),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 4),
            random_state=42,
        )
        cv = min(3, len(y))
        scores = cross_val_score(model, X, y, cv=cv, scoring="neg_mean_squared_error")
        return scores.mean()

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    best_params = study.best_params
    best_model = RandomForestRegressor(**best_params, random_state=42)
    best_model.fit(X, y)
    return best_model


def train_catboost(df: pd.DataFrame, target: str = "risk"):
    """Train a CatBoost model if library is installed."""
    try:
        from catboost import CatBoostRegressor
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("catboost is not installed") from exc
    cols = ["temp", "humidity", "wind_speed"]
    if "brightness" in df.columns:
        cols.append("brightness")
    X, y = df[cols], df[target]
    model = CatBoostRegressor(verbose=0)
    model.fit(X, y)
    return model


def train_lstm(df: pd.DataFrame, target: str = "risk", epochs: int = 10):
    """Train a simple LSTM network using TensorFlow."""
    try:
        import tensorflow as tf
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("tensorflow is not installed") from exc
    cols = ["temp", "humidity", "wind_speed"]
    if "brightness" in df.columns:
        cols.append("brightness")
    X = df[cols].values.astype("float32")
    y = df[target].values.astype("float32")
    X = X.reshape((X.shape[0], 1, X.shape[1]))
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(1, X.shape[2])),
        tf.keras.layers.LSTM(16, activation="relu"),
        tf.keras.layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=epochs, verbose=0)
    return model


def predict_with_model(model: RandomForestRegressor, df: pd.DataFrame) -> pd.Series:
    """Predict risk using a trained model."""
    cols = ["temp", "humidity", "wind_speed"]
    if "brightness" in df.columns:
        cols.append("brightness")
    features = df[cols]
    preds = model.predict(features)
    return pd.Series(preds, index=df.index, name="risk_pred")


def save_model(model: RandomForestRegressor, path: str) -> None:
    """Serialize model to disk."""
    joblib.dump(model, path)


def load_model(path: str) -> RandomForestRegressor:
    """Load a previously saved model."""
    return joblib.load(path)
