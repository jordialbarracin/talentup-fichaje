"""
TalentUP Fichaje — Rate limiting helpers for clock endpoints.
Supports optional Redis-backed rate limiting via REDIS_URL env var.
Falls back to the original in-memory implementation when Redis is not configured.
"""
import os
import time as time_module
from collections import defaultdict
from typing import Optional

from fastapi import Request

# --- Redis (optional) ---
_redis_client = None
_redis_enabled = False

REDIS_URL = os.environ.get("REDIS_URL", "")


def _get_redis_client():
    """Lazy import/build redis client so the module loads even without redis installed."""
    global _redis_client, _redis_enabled
    if _redis_client is not None:
        return _redis_client
    if not REDIS_URL:
        _redis_enabled = False
        return None
    try:
        from redis.asyncio import from_url

        _redis_client = from_url(REDIS_URL, decode_responses=True)
        _redis_enabled = True
        return _redis_client
    except Exception:
        _redis_enabled = False
        _redis_client = None
        return None


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


async def check_rate_limit(key: str, max_count: int, window: int = WINDOW_SECONDS) -> bool:
    """
    Async rate-limit check. Returns True if the request is allowed, False otherwise.

    Uses Redis when REDIS_URL is configured: INCR a per-window key and set expiry.
    Falls back to an in-memory cleanup+check otherwise.
    """
    client = _get_redis_client()
    if client is not None:
        now = int(time_module.time())
        bucket = now // window
        redis_key = f"rate:{key}:{bucket}"
        try:
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, window)
            results = await pipe.execute()
            count = results[0]
            return count <= max_count
        except Exception:
            # Redis failure must not block clock endpoints; fall back to memory.
            return _cleanup_and_check(_pin_limits, key, max_count, window)
    return _cleanup_and_check(_pin_limits, key, max_count, window)


async def record_rate(key: str):
    """
    Record a request hit for the current window.

    Uses Redis INCR when REDIS_URL is configured; otherwise stores in memory.
    """
    client = _get_redis_client()
    if client is not None:
        now = int(time_module.time())
        bucket = now // WINDOW_SECONDS
        redis_key = f"rate:{key}:{bucket}"
        try:
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, WINDOW_SECONDS)
            await pipe.execute()
            return
        except Exception:
            pass
    _record(_pin_limits, key)
