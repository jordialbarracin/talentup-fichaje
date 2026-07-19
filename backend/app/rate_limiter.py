"""
TalentUP Fichaje — Rate limiting helpers for clock endpoints.
"""
import time as time_module
from collections import defaultdict
from typing import Optional

from fastapi import Request

# One independent store per clock method. Key = f"{ip}:{tenant_id}".
_pin_limits: dict[str, list[float]] = defaultdict(list)
_nfc_limits: dict[str, list[float]] = defaultdict(list)
_qr_limits: dict[str, list[float]] = defaultdict(list)
# PIN failure tracking remains per IP+tenant (failed attempts are not tied to employee_id)
_pin_failures: dict[str, list[float]] = defaultdict(list)
# PIN blocks: key = f"{ip}:{tenant_id}" -> unblock timestamp
_pin_blocks: dict[str, float] = {}

CLOCK_MAX_PER_MINUTE = 10
PIN_FAIL_MAX_PER_MINUTE = 5
PIN_BLOCK_MINUTES = 5
WINDOW_SECONDS = 60


def _cleanup_and_check(
    store: dict[str, list[float]],
    key: str,
    max_count: int,
    window: int = WINDOW_SECONDS,
) -> bool:
    """Remove entries older than `window` seconds and check if under limit."""
    now = time_module.time()
    if key in store:
        store[key] = [t for t in store[key] if now - t < window]
    return len(store.get(key, [])) < max_count


def _record(store: dict[str, list[float]], key: str):
    store[key].append(time_module.time())


def _rate_limit_key(request: Request, tenant_id: Optional[str]) -> str:
    """Build rate-limit key from IP and tenant."""
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{tenant_id or 'unknown'}"
