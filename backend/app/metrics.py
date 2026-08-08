"""
TalentUP Fichaje — Prometheus metrics definitions and app-level counters.
"""
import time
from datetime import datetime, timezone

from prometheus_client import Counter, Histogram, Gauge

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf")],
)

ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of HTTP requests currently being processed",
)


# ── App-level daily counters (JSON /api/metrics endpoint) ───────────────────
# Tracks total requests and errors today, reset daily. In-memory only; suitable
# for a single-process deployment. The UTC date string is used as the day key.

class _DailyCounters:
    """Simple in-memory daily request/error counters."""

    def __init__(self):
        self._date: str = self._today()
        self._requests: int = 0
        self._errors: int = 0

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _maybe_reset(self):
        today = self._today()
        if today != self._date:
            self._date = today
            self._requests = 0
            self._errors = 0

    def record_request(self):
        self._maybe_reset()
        self._requests += 1

    def record_error(self):
        self._maybe_reset()
        self._errors += 1

    def snapshot(self) -> dict:
        self._maybe_reset()
        return {"date": self._date, "requests": self._requests, "errors": self._errors}


daily_counters = _DailyCounters()

# Process start time for uptime metric (set once at import).
PROCESS_START_TIME = time.time()
