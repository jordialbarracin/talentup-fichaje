"""
TalentUP Fichaje — Database connection.
Async SQLAlchemy with PostgreSQL support, SQLite fallback for development.
"""
import os
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


async def init_db():
    """Create all tables. Safe to call on every startup (no-op if exist)."""
    async with engine.begin() as conn:
        from app.database import Base
        from app.models import (  # noqa: F401 — ensure models are imported so tables register
            Tenant, User, Employee, Shift, Schedule, ClockIn, Incident, AuditLog
        )
        await conn.run_sync(Base.metadata.create_all)
