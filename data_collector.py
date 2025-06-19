from pathlib import Path
from typing import Optional
from pandas import DataFrame
import structlog

from dotenv import load_dotenv

from collector.logging_config import setup_logging
from risk_analyzer import add_risk_column
from notifier import alert_high_risk

from collector import (
    append_json,
    clean,
    fetch_latest_weather,
    normalize,
    save_csv,
    append_to_db,
    append_to_ts,
    CollectorConfig,
    load_config,
    upload_file,
)
logger = structlog.get_logger(__name__)


def fetch_weather(
    district: Optional[str] = None, config: CollectorConfig | None = None
) -> DataFrame:
    """Fetch and preprocess weather data."""
    df = fetch_latest_weather(config)
    df = normalize(df)
    if district:
        df = df[df["district"].str.lower() == district.lower()]
    df = clean(df)
    return df


def collect_and_save(
    json_output: Path,
    csv_output: Optional[Path] = None,
    db_output: Optional[Path] = None,
    db_url: str | None = None,
    s3_bucket: str | None = None,
    s3_key: str | None = None,
    district: Optional[str] = None,
    config: CollectorConfig | None = None,
) -> None:
    """Fetch weather data and save it in various formats."""
    df = fetch_weather(district, config)
    append_json(df, json_output)
    if csv_output:
        save_csv(df, csv_output)
    if db_output:
        append_to_db(df, db_output)
    if db_url:
        append_to_ts(df, db_url)
    if s3_bucket:
        upload_file(json_output, s3_bucket, s3_key)
    df = add_risk_column(df)
    alert_high_risk(df)
    logger.info("Saved %d records to %s", len(df), json_output)
    if csv_output:
        logger.info("CSV saved to %s", csv_output)
    if db_output:
        logger.info("Database updated at %s", db_output)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect latest weather data from MGM"
    )
    parser.add_argument(
        "--output", default="weather_data.json", help="Path to output JSON file"
    )
    parser.add_argument("--csv", help="Optional CSV output path")
    parser.add_argument("--db", help="Optional SQLite database path")
    parser.add_argument("--db-url", help="TimescaleDB connection URL")
    parser.add_argument("--s3-bucket", help="Upload output to this S3 bucket")
    parser.add_argument("--s3-key", help="Key name when uploading to S3")
    parser.add_argument("--district", help="Filter for specific district")
    defaults = load_config()
    parser.add_argument("--retries", type=int, default=defaults.retries, help="Number of fetch retries")
    parser.add_argument("--retry-delay", type=int, default=defaults.retry_delay, help="Seconds between retries")
    parser.add_argument("--url", default=defaults.mgm_url, help="MGM API URL")
    args = parser.parse_args()

    load_dotenv()
    setup_logging()

    json_path = Path(args.output)
    csv_path = Path(args.csv) if args.csv else None
    db_path = Path(args.db) if args.db else None
    db_url = args.db_url
    config = CollectorConfig(
        mgm_url=args.url, retries=args.retries, retry_delay=args.retry_delay
    )
    collect_and_save(
        json_path,
        csv_output=csv_path,
        db_output=db_path,
        db_url=db_url,
        s3_bucket=args.s3_bucket,
        s3_key=args.s3_key,
        district=args.district,
        config=config,
    )


if __name__ == "__main__":
    main()
