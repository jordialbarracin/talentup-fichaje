"""
TalentUP Fichaje — Prometheus metrics definitions.
"""
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
