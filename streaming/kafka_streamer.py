import json
import time
from pathlib import Path
from typing import Iterator

import pandas as pd
import structlog
from kafka import KafkaProducer, KafkaConsumer

from collector import append_to_db, fetch_latest_weather, normalize, clean

logger = structlog.get_logger(__name__)


def produce_weather(
    df: pd.DataFrame,
    topic: str = "weather",
    servers: str = "localhost:9092",
) -> None:
    """Publish weather records to Kafka."""
    producer = KafkaProducer(
        bootstrap_servers=servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    for record in df.to_dict(orient="records"):
        producer.send(topic, record)
    producer.flush()
    producer.close()
    logger.info("published_records", count=len(df), topic=topic)


def consume_weather(
    topic: str = "weather",
    servers: str = "localhost:9092",
    group_id: str = "weather-group",
) -> Iterator[pd.DataFrame]:
    """Yield weather dataframes from Kafka."""
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=servers,
        auto_offset_reset="earliest",
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    for msg in consumer:
        yield pd.DataFrame([msg.value])


def stream_to_kafka(
    interval: int = 60,
    topic: str = "weather",
    servers: str = "localhost:9092",
) -> None:
    """Continuously fetch weather data and publish to Kafka."""
    while True:
        df = fetch_latest_weather()
        df = normalize(df)
        df = clean(df)
        if not df.empty:
            produce_weather(df, topic=topic, servers=servers)
        time.sleep(interval)


def consume_to_db(
    db_path: Path,
    topic: str = "weather",
    servers: str = "localhost:9092",
) -> None:
    """Consume weather data from Kafka and append to SQLite."""
    for df in consume_weather(topic=topic, servers=servers):
        append_to_db(df, db_path)
        logger.info("stored_records", count=len(df), db=str(db_path))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kafka streaming utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    prod = sub.add_parser("stream_to_kafka")
    prod.add_argument("--topic", default="weather")
    prod.add_argument("--servers", default="localhost:9092")
    prod.add_argument("--interval", type=int, default=60)

    cons = sub.add_parser("consume_to_db")
    cons.add_argument("--db", required=True)
    cons.add_argument("--topic", default="weather")
    cons.add_argument("--servers", default="localhost:9092")

    args = parser.parse_args()

    if args.cmd == "stream_to_kafka":
        stream_to_kafka(interval=args.interval, topic=args.topic, servers=args.servers)
    elif args.cmd == "consume_to_db":
        consume_to_db(Path(args.db), topic=args.topic, servers=args.servers)
