"""
TalentUP Fichaje — FastAPI Application.
"""
import os
import sys
import time
import uuid
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Default to SQLite for local dev — set before importing database module
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./talentup_fichaje.db")

# Default log level
os.environ.setdefault("LOG_LEVEL", "INFO")

from app.logging_config import configure_logging, get_logger, log_request
from app.database import init_db, engine
from app.routers import (
    auth,
    employees,
    shifts,
    schedules,
    clock,
    reports,
    tenants,
    contracts,
    holidays,
    vacations,
    leave,
    overtime,
    payroll,
    notifications,
    calendar,
    incidents,
    settings,
    billing,
    devices,
)

# ── Bootstrap logging ───────────────────────────────────────────────────────
configure_logging()
logger = get_logger(__name__)

# ── Process start time for uptime metric ───────────────────────────────────
_START_TIME = time.time()
APP_VERSION = "2.0.0"


# ── Redis helper (lazy) ─────────────────────────────────────────────────────
def _is_production() -> bool:
    env = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "")).lower()
    return env in {"production", "prod"}


def _get_redis_client():
    """Devuelve un cliente Redis si está disponible y configurado; si no, None.

    En producción REDIS_URL es obligatoria: si no está configurada, falla
    el arranque con un error claro.
    """
    redis_url = os.environ.get("REDIS_URL", "")
    if not redis_url:
        if _is_production():
            raise RuntimeError("REDIS_URL requerido en produccion")
        return None
    try:
        import redis as _redis
        return _redis.from_url(redis_url, socket_connect_timeout=2)
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables if they don't exist (SQLite dev mode)."""
    logger.info("application_starting", extra={"version": APP_VERSION})
    await init_db()
    yield
    # Shutdown: dispose engine
    await engine.dispose()
    logger.info("application_stopped")


app = FastAPI(
    title="TalentUP Fichaje API",
    description="SaaS de fichaje digital para hostelería. Multi-tenant. Cumple RD-ley 8/2019.",
    version=APP_VERSION,
    lifespan=lifespan,
)

# Body size limit middleware (1 MB)
MAX_BODY_SIZE = 1 * 1024 * 1024

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Generate a per-request nonce so we can enforce a strict CSP without
        # 'unsafe-inline'. HTML responses must inject the nonce into any inline
        # <script> / <style> tags. See `add_csp_nonce` below.
        request.state.csp_nonce = secrets.token_urlsafe(16)
        response = await call_next(request)
        nonce = request.state.csp_nonce
        csp = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response


# Helper to inject the CSP nonce into HTML responses served by FastAPI.
# Static HTML files (e.g. Vite-built apps) should add nonce="{{ nonce }}"
# server-side or be served through this middleware.
def add_csp_nonce(html_content: str, nonce: str) -> str:
    """Add nonce attribute to inline <script> tags that don't already have one."""
    import re
    return re.sub(
        r'(<script(?![^>]*\snonce=)[^>]*\u003e)',
        lambda m: m.group(1).replace('>', f' nonce="{nonce}">'),
        html_content,
        flags=re.IGNORECASE,
    )


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if len(body) > MAX_BODY_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Body too large"},
                )
        return await call_next(request)


@app.middleware("http")
async def body_size_limit(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
        if len(body) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Body too large"},
            )
    return await call_next(request)

# Keep legacy http middleware for compatibility; add BaseHTTPMiddleware classes next.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware)

# CORS — allow specific origins from env var
_cors_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001",
)
allow_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ───────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request with method, path, status and duration."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_failed",
            extra={
                "event": "request_error",
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
                "request_id": request_id,
                "error": str(exc),
            },
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    # No loggear health checks tan verbosamente en prod
    if request.url.path != "/api/health" or os.environ.get("LOG_LEVEL", "").upper() == "DEBUG":
        log_request(
            logger=logger,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
        )
    response.headers["x-request-id"] = request_id
    return response


# ── Exception logging ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log unhandled exceptions and return a generic 500."""
    request_id = getattr(request.state, "request_id", "-")
    logger.exception(
        "unhandled_exception",
        extra={
            "event": "unhandled_exception",
            "method": request.method,
            "path": request.url.path,
            "request_id": request_id,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor",
            "request_id": request_id,
        },
    )


# ── Deep health check ────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    """Health check profundo: DB SELECT 1, Redis ping y uptime."""
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(_START_TIME))
    uptime_seconds = round(time.time() - _START_TIME)

    checks = {
        "status": "ok",
        "service": "TalentUP Fichaje API",
        "version": APP_VERSION,
        "started_at": started_at,
        "uptime_seconds": uptime_seconds,
        "db_status": "unknown",
        "redis_status": "unknown",
    }

    healthy = True

    # DB check
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db_status"] = "ok"
    except Exception as exc:
        healthy = False
        checks["db_status"] = "error"
        checks["db_error"] = str(exc)
        logger.error("health_check_db_failed", extra={"error": str(exc)})

    # Redis check
    redis_client = _get_redis_client()
    if redis_client is None:
        checks["redis_status"] = "disabled"
    else:
        try:
            redis_client.ping()
            checks["redis_status"] = "ok"
        except Exception as exc:
            healthy = False
            checks["redis_status"] = "error"
            checks["redis_error"] = str(exc)
            logger.error("health_check_redis_failed", extra={"error": str(exc)})

    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    if not healthy:
        checks["status"] = "degraded"

    return JSONResponse(status_code=status_code, content=checks)


# Register routers
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(shifts.router)
app.include_router(schedules.router)
app.include_router(clock.router)
app.include_router(clock.ws_router)
app.include_router(reports.router)
app.include_router(tenants.router)
app.include_router(contracts.router)
app.include_router(holidays.router)
app.include_router(vacations.router)
app.include_router(leave.router)
app.include_router(overtime.router)
app.include_router(payroll.router)
app.include_router(notifications.router)
app.include_router(calendar.router)
app.include_router(incidents.router)
app.include_router(settings.router)
app.include_router(billing.router)
app.include_router(devices.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
