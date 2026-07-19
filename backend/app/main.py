"""
TalentUP Fichaje — FastAPI Application.
"""
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Default to SQLite for local dev — set before importing database module
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./talentup_fichaje.db")

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
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables if they don't exist (SQLite dev mode)."""
    await init_db()
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="TalentUP Fichaje API",
    description="SaaS de fichaje digital para hostelería. Multi-tenant. Cumple RD-ley 8/2019.",
    version="2.0.0",
    lifespan=lifespan,
)

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

# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "TalentUP Fichaje API", "version": "2.0.0"}

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
