from dataclasses import dataclass
import os

@dataclass
class CollectorConfig:
    """Configuration for MGM API access."""

    mgm_url: str = os.getenv("MGM_API_URL", "https://api.mgm.gov.tr/api/sonDurumlar")
    retries: int = int(os.getenv("MGM_RETRIES", "3"))
    retry_delay: int = int(os.getenv("MGM_RETRY_DELAY", "5"))

def load_config() -> CollectorConfig:
    """Load configuration from environment variables."""
    return CollectorConfig()
