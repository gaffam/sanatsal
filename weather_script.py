#!/usr/bin/env python
"""Simple weather fetcher using MGM API."""
from pathlib import Path
import structlog

from collector.logging_config import setup_logging
from collector import fetch_latest_weather, normalize, clean, append_json


def main() -> None:
    setup_logging()
    logger = structlog.get_logger(__name__)
    df = fetch_latest_weather()
    df = normalize(df)
    df = clean(df)
    append_json(df, Path("weather_data.json"))
    logger.info("Fetched %d records", len(df))
    print(df)


if __name__ == "__main__":
    main()
