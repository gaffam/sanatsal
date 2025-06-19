import os
import io
import structlog
import pandas as pd
import requests
from requests.exceptions import RequestException

MODIS_URL = os.getenv(
    "MODIS_URL",
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/MODIS?country=Turkey",
)
VIIRS_URL = os.getenv(
    "VIIRS_URL",
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/VIIRS_SNPP_NRT?country=Turkey",
)
SENTINEL_URL = os.getenv(
    "SENTINEL_URL",
    "https://sentinel.example.com/api/fire.csv?country=Turkey",
)
EFFIS_URL = os.getenv(
    "EFFIS_URL",
    "https://effis.example.com/api/fire.csv?country=Turkey",
)

logger = structlog.get_logger(__name__)


def _fetch_csv(url: str, source: str) -> pd.DataFrame:
    """Fetch CSV data from a satellite source."""
    logger.info("fetching_satellite", source=source, url=url)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except RequestException as exc:
        logger.error("satellite_failed", source=source, error=str(exc))
        raise
    return pd.read_csv(io.StringIO(response.text))


def fetch_modis_data(url: str = MODIS_URL) -> pd.DataFrame:
    """Fetch MODIS fire data and return as DataFrame."""
    return _fetch_csv(url, "modis")


def fetch_viirs_data(url: str = VIIRS_URL) -> pd.DataFrame:
    """Fetch VIIRS fire data and return as DataFrame."""
    return _fetch_csv(url, "viirs")


def fetch_sentinel2_data(url: str = SENTINEL_URL) -> pd.DataFrame:
    """Fetch Sentinel-2 fire observations."""
    return _fetch_csv(url, "sentinel2")


def fetch_effis_data(url: str = EFFIS_URL) -> pd.DataFrame:
    """Fetch EFFIS fire data."""
    return _fetch_csv(url, "effis")
