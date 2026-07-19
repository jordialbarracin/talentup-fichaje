"""TalentUP Fichaje — Database connection.
Async SQLAlchemy with PostgreSQL support, SQLite fallback for development.

Migration strategy:
- Production (PostgreSQL): uses Alembic migrations via `alembic upgrade head`
- Development (SQLite): uses create_all() for simplicity and seed compatibility
"""
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Default to SQLite for local dev — no PostgreSQL required
DEFAULT_DB_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./talentup_fichaje.db",
)

DATABASE_URL = DEFAULT_DB_URL

# If the URL is postgresql:// (without +asyncpg), fix it
if DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def _is_sqlite(url: str) -> bool:
    """Check if the database URL points to a SQLite database."""
    return "sqlite" in url


async def init_db():
    """Create all tables or run migrations depending on environment.

    - In development (SQLite): uses create_all() — simple, no-op if tables exist.
    - In production (PostgreSQL): runs `alembic upgrade head` via subprocess.
    """
    if _is_sqlite(DATABASE_URL):
        # Development: use create_all() — keeps seed and tests working
        async with engine.begin() as conn:
            from app.database import Base
            from app.models import (  # noqa: F401 — ensure models are imported so tables register
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
