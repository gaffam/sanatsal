import time
import structlog

from .metrics import WEATHER_FETCH_ERRORS, WEATHER_FETCH_TOTAL
from .config import CollectorConfig, load_config

import pandas as pd
import requests
from requests.exceptions import RequestException

logger = structlog.get_logger(__name__)


def fetch_latest_weather(config: CollectorConfig | None = None) -> pd.DataFrame:
    """Fetch latest weather data from MGM API with retry logic."""
    if config is None:
        config = load_config()
    logger.info("Fetching weather data from MGM API", url=config.mgm_url)
    for attempt in range(config.retries):
        try:
            response = requests.get(config.mgm_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            WEATHER_FETCH_TOTAL.inc()
            return pd.DataFrame(data)
        except RequestException as exc:
            WEATHER_FETCH_ERRORS.inc()
            logger.warning(
                "Failed to fetch MGM data (attempt %d/%d): %s",
                attempt + 1,
                config.retries,
                exc,
            )
            if attempt + 1 < config.retries:
                logger.info("Retrying in %d seconds...", config.retry_delay)
                time.sleep(config.retry_delay)
            else:
                logger.error("All retries failed. Giving up.")
                raise
    raise RuntimeError("Failed to fetch data after multiple retries.")
