"""
TalentUP Fichaje — Configuración de logging estructurado JSON.

Usa python-json-logger cuando esté disponible; si no, cae a un formato
legible para desarrollo. En producción (APP_ENV=production) se fuerza JSON.

Niveles:
- DEBUG: visible solo en desarrollo cuando LOG_LEVEL=DEBUG.
- INFO:  logs operativos (requests, auth, clock, health) en prod.
- WARNING/ERROR: siempre visibles.
"""
import logging
import os
import sys
import time
from typing import Any

_APP_ENV = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "development")).lower()
_IS_PROD = _APP_ENV in {"production", "prod", "staging"}
_LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG" if not _IS_PROD else "INFO").upper()


def _build_formatter() -> logging.Formatter:
    """Construye el formatter adecuado según entorno y librerías instaladas."""
    # Preferir JSON en producción o si se fuerza explícitamente
    force_json = os.environ.get("LOG_FORMAT", "auto").lower() == "json"

    if _IS_PROD or force_json:
        try:
            from pythonjsonlogger.jsonlogger import JsonFormatter

            # Campos útiles para observabilidad (Loki, Datadog, CloudWatch...)
            fmt = (
                "%(asctime)s %(levelname)s %(name)s %(message)s "
                "%(funcName)s %(pathname)s:%(lineno)d "
                "%(request_id)s %(user_id)s %(tenant_id)s"
            )
            return JsonFormatter(
                fmt,
                rename_fields={
                    "asctime": "timestamp",
                    "levelname": "level",
                    "funcName": "func_name",
                    "pathname": "path",
                },
                timestamp=True,
            )
        except Exception:  # pragma: no cover - fallback si no está instalado
            pass

    # Fallback legible para desarrollo
    return logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _normalize_level(level: str) -> int:
    """Convierte un string de nivel a su constante logging."""
    return getattr(logging, level.upper(), logging.INFO)


def configure_logging() -> None:
    """Configura el logger raíz y ajusta niveles de librerías ruidosas."""
    root = logging.getLogger()
    root.setLevel(_normalize_level(_LOG_LEVEL))

    # Evitar duplicados si se reconfigura
    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_build_formatter())
    root.addHandler(handler)

    # Librerías ruidosas: dejarlas en WARNING salvo que LOG_LEVEL sea DEBUG
    if _LOG_LEVEL != "DEBUG":
        for noisy in ("sqlalchemy.engine", "uvicorn.access", "uvicorn.error"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    # Siempre mostrar nuestros módulos principales según el nivel configurado
    for module in ("app", "app.auth", "app.routers.auth", "app.routers.clock"):
        logging.getLogger(module).setLevel(_normalize_level(_LOG_LEVEL))


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con el nombre indicado."""
    return logging.getLogger(name)


# ── Contexto extra para logs estructurados ───────────────────────────────────

class _ContextFilter(logging.Filter):
    """Filtro que inyecta campos de contexto si el LogRecord no los tiene."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, default in (
            ("request_id", "-"),
            ("user_id", "-"),
            ("tenant_id", "-"),
        ):
            if not hasattr(record, key) or getattr(record, key) is None:
                setattr(record, key, default)
        return True


def _inject_context_filter() -> None:
    root = logging.getLogger()
    for handler in root.handlers:
        if not any(isinstance(f, _ContextFilter) for f in handler.filters):
            handler.addFilter(_ContextFilter())


# Hook: inyectar el filtro tras configurar
_inject_context_filter()


# ── Helpers de logging semántico ─────────────────────────────────────────────

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str = "-",
    tenant_id: str = "-",
    request_id: str = "-",
) -> None:
    """Log estructurado de una petición HTTP."""
    extra = {
        "event": "request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "user_id": user_id,
        "tenant_id": tenant_id,
        "request_id": request_id,
    }
    logger.info("request", extra=extra)


def log_auth_event(
    logger: logging.Logger,
    event: str,
    success: bool,
    email: str = "-",
    user_id: str = "-",
    tenant_id: str = "-",
    request_id: str = "-",
) -> None:
    """Log estructurado de eventos de autenticación (login, register, logout)."""
    extra = {
        "event": f"auth.{event}",
        "success": success,
        "email": email,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "request_id": request_id,
    }
    if success:
        logger.info("auth_event", extra=extra)
    else:
        logger.warning("auth_event", extra=extra)


def log_clock_event(
    logger: logging.Logger,
    clock_type: str,
    employee_id: str,
    tenant_id: str,
    success: bool,
    error: str | None = None,
    request_id: str = "-",
) -> None:
    """Log estructurado de eventos de fichaje (PIN/NFC/QR)."""
    extra = {
        "event": "clock",
        "clock_type": clock_type,
        "employee_id": employee_id,
        "tenant_id": tenant_id,
        "success": success,
        "request_id": request_id,
    }
    if error:
        extra["error"] = error
    if success:
        logger.info("clock_event", extra=extra)
    else:
        logger.warning("clock_event", extra=extra)


def log_error(
    logger: logging.Logger,
    message: str,
    exc_info: Any = None,
    **context: Any,
) -> None:
    """Log estructurado de errores con contexto libre."""
    extra = {"event": "error", **context}
    logger.error(message, extra=extra, exc_info=exc_info)
