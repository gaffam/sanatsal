from prometheus_client import Counter

WEATHER_FETCH_TOTAL = Counter(
    "weather_fetch_total", "Total successful weather fetches"
)
WEATHER_FETCH_ERRORS = Counter(
    "weather_fetch_errors_total", "Total weather fetch errors"
)
