"""TalentUP Fichaje — Database connection.
Async SQLAlchemy with PostgreSQL required in production, SQLite allowed
for development/testing only.

Migration strategy:
- Production (PostgreSQL): uses Alembic migrations via `alembic upgrade head`
- Development (SQLite): uses create_all() for simplicity and seed compatibility
"""
import os
import sys
from contextvars import ContextVar
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

_ENV = os.environ.get("APP_ENV", os.environ.get("ENVIRONMENT", "")).lower()
_DATABASE_URL = os.environ.get("DATABASE_URL", "")


# Per-request tenant id used by get_db to configure the PostgreSQL session.
tenant_id_ctx: ContextVar[str | None] = ContextVar("tenant_id_ctx", default=None)


def _is_sqlite(url: str) -> bool:
    """Check if the database URL points to a SQLite database."""
    return "sqlite" in url


def _is_postgresql(url: str) -> bool:
    """Check if the database URL points to a PostgreSQL database."""
    return "postgresql" in url


def _is_production() -> bool:
    """True when the runtime environment is considered production."""
    return _ENV in {"production", "prod"}


def _resolve_database_url() -> str:
    """Resolve and validate DATABASE_URL based on the environment.

    Rules:
    - If DATABASE_URL contains 'sqlite', use SQLite (dev/tests only).
    - If DATABASE_URL contains 'postgresql', use PostgreSQL.
    - If DATABASE_URL is not set, raise a clear error requiring configuration.
    """
    if _is_sqlite(_DATABASE_URL):
        return _DATABASE_URL

    if _is_postgresql(_DATABASE_URL):
        # Normalise plain postgresql:// to the asyncpg driver
        url = _DATABASE_URL
        if "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    if not _DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL requerido. Configura PostgreSQL o SQLite para desarrollo."
        )

    # Any other unsupported scheme
    raise RuntimeError(
        f"Esquema de base de datos no soportado: {_DATABASE_URL}. "
        "Usa 'sqlite' para desarrollo/pruebas o 'postgresql' para produccion."
    )


DATABASE_URL = _resolve_database_url()

if _is_postgresql(DATABASE_URL):
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=40,
        pool_timeout=30,
        pool_recycle=1800,
    )
else:
    engine = create_async_engine(DATABASE_URL, echo=False)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def _set_tenant_context(db: AsyncSession) -> None:
    """Set the PostgreSQL session-level tenant id used by RLS policies.

    SQLite does not support RLS, so this is a no-op there.
    """
    if not _is_postgresql(DATABASE_URL):
        return

    tenant_id = tenant_id_ctx.get()
    if tenant_id:
        await db.execute(text(f"SET app.tenant_id = '{tenant_id}'"))
    else:
        await db.execute(text("SET app.tenant_id = ''"))


async def get_db():
    """FastAPI dependency that yields an async DB session.

    On PostgreSQL it also sets the `app.tenant_id` configuration variable
    so that Row Level Security policies filter rows by tenant.
    """
    async with async_session_factory() as session:
        try:
            await _set_tenant_context(session)
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables or run migrations depending on environment.

    - In development (SQLite): uses create_all() — simple, no-op if tables exist.
    - In production (PostgreSQL): runs `alembic upgrade head` via subprocess.
    """
    if _is_sqlite(DATABASE_URL):
        # Development: use create_all() — keeps seed and tests working
        async with engine.begin() as conn:
            from app.database import Base
            from app.models import (  # noqa: F401 - ensure models are imported so tables register
                Tenant, User, Employee, Shift, Schedule, ClockIn, Incident, AuditLog,
                VacationRequest, Leave, Holiday,
                Contract, Overtime, Payroll, Notification, WorkCalendar,
                Geofence, DocumentTemplate, BillingRecord,
            )
            await conn.run_sync(Base.metadata.create_all)
    else:
        # Production: run Alembic migrations
        import subprocess
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Alembic migration failed:\n{result.stderr}\n{result.stdout}"
            )
