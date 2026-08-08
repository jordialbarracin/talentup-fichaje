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
_login_limits: dict[str, list[float]] = defaultdict(list)
# Tenant-level hourly clock rate limit. Key = tenant_id only (IP-agnostic).
# Caps total fichajes per tenant to CLOCK_TENANT_MAX_PER_HOUR per hour,
# in addition to the per-IP+tenant minute limits above.
_tenant_clock_limits: dict[str, list[float]] = defaultdict(list)
# PIN failure tracking remains per IP+tenant (failed attempts are not tied to employee_id)
_pin_failures: dict[str, list[float]] = defaultdict(list)
# PIN blocks: key = f"{ip}:{tenant_id}" -> unblock timestamp
_pin_blocks: dict[str, float] = {}

CLOCK_MAX_PER_MINUTE = 10
PIN_FAIL_MAX_PER_MINUTE = 5
PIN_BLOCK_MINUTES = 5
WINDOW_SECONDS = 60
# Tenant-level hourly limit: max 100 fichajes per hour per tenant (any IP/method).
CLOCK_TENANT_MAX_PER_HOUR = 100
CLOCK_TENANT_WINDOW_SECONDS = 3600


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
    if key not in store:
        store[key] = []
    store[key].append(time_module.time())


def _rate_limit_key(request: Request, tenant_id: Optional[str]) -> str:
    """Build rate-limit key from IP and tenant."""
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{tenant_id or 'unknown'}"


def _method_store(method: str) -> dict[str, list[float]]:
    """Return the in-memory fallback store matching the rate-limit method."""
    if method == "nfc":
        return _nfc_limits
    if method == "qr":
        return _qr_limits
    if method == "login":
        return _login_limits
    return _pin_limits


async def check_rate_limit(key: str, max_count: int, window: int = WINDOW_SECONDS, method: str = "global") -> bool:
    """
    Async rate-limit check. Returns True if the request is allowed, False otherwise.

    Uses Redis when REDIS_URL is configured: INCR a per-window key and set expiry.
    Falls back to an in-memory cleanup+check otherwise.
    """
    client = _get_redis_client()
    if client is not None:
        now = int(time_module.time())
        bucket = now // window
        redis_key = f"rate:{method}:{key}:{bucket}"
        try:
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, window)
            results = await pipe.execute()
            count = results[0]
            return count <= max_count
        except Exception:
            # Redis failure must not block clock endpoints; fall back to memory.
            return _cleanup_and_check(_method_store(method), key, max_count, window)
    return _cleanup_and_check(_method_store(method), key, max_count, window)


async def record_rate(key: str, method: str = "global"):
    """
    Record a request hit for the current window.

    Uses Redis INCR when REDIS_URL is configured; otherwise stores in memory.
    """
    client = _get_redis_client()
    if client is not None:
        now = int(time_module.time())
        bucket = now // WINDOW_SECONDS
        redis_key = f"rate:{method}:{key}:{bucket}"
        try:
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, WINDOW_SECONDS)
            await pipe.execute()
            return
        except Exception:
            pass
    _record(_method_store(method), key)


def _check_and_record(store: dict[str, list[float]], key: str, max_count: int, window: int) -> bool:
    """In-memory rate limit check that also records the current hit atomically."""
    allowed = _cleanup_and_check(store, key, max_count, window)
    _record(store, key)
    return allowed


async def check_and_record_rate(key: str, max_count: int, window: int = WINDOW_SECONDS, method: str = "global") -> bool:
    """Unified rate-limit check + record. Always records the request when in-memory."""
    client = _get_redis_client()
    if client is not None:
        now = int(time_module.time())
        bucket = now // window
        redis_key = f"rate:{method}:{key}:{bucket}"
        try:
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, window)
            results = await pipe.execute()
            count = results[0]
            return count <= max_count
        except Exception:
            return _check_and_record(_method_store(method), key, max_count, window)
    return _check_and_record(_method_store(method), key, max_count, window)


# --- PIN failure / block helpers (async, Redis-aware with in-memory fallback) ---
async def is_pin_blocked(key: str) -> tuple[bool, int]:
    """Return (blocked, remaining_seconds). Uses Redis when available."""
    client = _get_redis_client()
    if client is not None:
        redis_key = f"pin:block:{key}"
        try:
            ttl = await client.ttl(redis_key)
            if ttl > 0:
                return True, ttl
            return False, 0
        except Exception:
            pass
    now = time_module.time()
    if key in _pin_blocks and now < _pin_blocks[key]:
        remaining = int(_pin_blocks[key] - now)
        return True, remaining
    if key in _pin_blocks:
        del _pin_blocks[key]
    return False, 0


async def check_pin_block(key: str) -> bool:
    """Return True if the key is currently PIN-blocked."""
    blocked, _ = await is_pin_blocked(key)
    return blocked


async def record_pin_failure(key: str) -> bool:
    """
    Record a failed PIN attempt. Return True if the key should be blocked now.
    Uses Redis when available; otherwise stores in memory.
    """
    client = _get_redis_client()
    if client is not None:
        now = int(time_module.time())
        bucket = now // WINDOW_SECONDS
        fail_key = f"pin:fail:{key}:{bucket}"
        block_key = f"pin:block:{key}"
        try:
            pipe = client.pipeline()
            pipe.incr(fail_key)
            pipe.expire(fail_key, WINDOW_SECONDS)
            pipe.exists(block_key)
            results = await pipe.execute()
            count = results[0]
            already_blocked = bool(results[2])
            if count >= PIN_FAIL_MAX_PER_MINUTE and not already_blocked:
                await client.setex(block_key, PIN_BLOCK_MINUTES * 60, "1")
                return True
            return False
        except Exception:
            pass

    # In-memory fallback
    now = time_module.time()
    if key in _pin_failures:
        _pin_failures[key] = [t for t in _pin_failures[key] if now - t < WINDOW_SECONDS]
    _pin_failures[key].append(now)
    if len(_pin_failures[key]) >= PIN_FAIL_MAX_PER_MINUTE:
        _pin_blocks[key] = now + PIN_BLOCK_MINUTES * 60
        return True
    return False


# ── Tenant-level hourly rate limit for clock endpoints ─────────────────────
# Max 100 fichajes per hour per tenant_id, independent of IP/method.
# Tracked in-memory only (Redis backend optional extension).
async def check_tenant_clock_rate(tenant_id: str) -> bool:
    """
    Check (without recording) whether the tenant is under the hourly limit.
    Returns True if allowed, False if the tenant has exceeded CLOCK_TENANT_MAX_PER_HOUR.
    """
    if not tenant_id:
        return True
    client = _get_redis_client()
    if client is not None:
        now = int(time_module.time())
        bucket = now // CLOCK_TENANT_WINDOW_SECONDS
        redis_key = f"rate:tenant_clock:{tenant_id}:{bucket}"
        try:
            count = await client.incr(redis_key)
            await client.expire(redis_key, CLOCK_TENANT_WINDOW_SECONDS)
            return count <= CLOCK_TENANT_MAX_PER_HOUR
        except Exception:
            pass
    # In-memory: cleanup + record atomically
    now = time_module.time()
    store = _tenant_clock_limits
    if tenant_id in store:
        store[tenant_id] = [t for t in store[tenant_id] if now - t < CLOCK_TENANT_WINDOW_SECONDS]
    store[tenant_id].append(now)
    return len(store[tenant_id]) <= CLOCK_TENANT_MAX_PER_HOUR
