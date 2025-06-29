import os
import logging
import requests

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

logger = logging.getLogger(__name__)


def send_slack_message(text: str) -> None:
    """Send a message to Slack if webhook is configured."""
    if not SLACK_WEBHOOK:
        logger.info("Slack webhook not configured; skipping alert")
        return
    try:
        requests.post(SLACK_WEBHOOK, json={"text": text}, timeout=10)
    except Exception as exc:
        logger.error("Failed to send Slack message: %s", exc)


def alert_high_risk(df, threshold: float = 10.0) -> None:
    """Send an alert when any risk value exceeds the threshold."""
    high = df[df.get("risk", 0) >= threshold]
    if not high.empty:
        send_slack_message(f"High fire risk detected for {len(high)} records!")
