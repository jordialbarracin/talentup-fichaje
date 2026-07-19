"""
TalentUP Fichaje — Test configuration.
In-memory SQLite database, seed data, async test client.
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone, time, date, timedelta

# Force in-memory SQLite BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.database import engine, async_session_factory, Base, get_db, init_db
from app.main import app
from app.models.tenant import Tenant
from app.models.user import User
from app.models.shift import Shift
from app.models.employee import Employee
from app.models.vacation_request import VacationRequest
from app.models.leave import Leave
from app.models.holiday import Holiday
from app.auth import hash_password, create_access_token, compute_pin_hash_fast


# ── Event loop ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Database ───────────────────────────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables before each test, drop after."""
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ── Seed data ───────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def seed_data():
    """Insert seed data and return references (ids, tokens, etc.)."""
    async with async_session_factory() as db:
        # 1. Super Admin
        admin = User(
            email="admin@talentup.es",
            password_hash=hash_password("admin123"),
            name="Admin TalentUP",
            role="super_admin",
            tenant_id=None,
        )
        db.add(admin)
        await db.flush()

        # 2. Tenant A
        tenant_a = Tenant(
            name="Restaurante La Tagliatella",
            legal_name="La Tagliatella SL",
            cif="B12345678",
            address="Calle Mayor 42, Madrid",
            phone="+34 912 345 678",
            email="info@latagliatella.es",
            convenio="hosteleria",
            tolerancia_min=5,
            plan="premium",
        )
        db.add(tenant_a)
        await db.flush()

        # 3. Tenant B (for cross-tenant isolation tests)
        tenant_b = Tenant(
            name="Bar El Puerto",
            legal_name="El Puerto SL",
            cif="B87654321",
            address="Calle Puerto 10, Barcelona",
            phone="+34 934 567 890",
            email="info@elpuerto.es",
            convenio="hosteleria",
            tolerancia_min=5,
            plan="basic",
        )
        db.add(tenant_b)
        await db.flush()

        # 4. Owner for Tenant A
        owner_a = User(
            tenant_id=tenant_a.id,
            email="owner@latagliatella.es",
            password_hash=hash_password("owner123"),
            name="María García",
            role="owner",
        )
        db.add(owner_a)
        await db.flush()

        # 5. Owner for Tenant B
        owner_b = User(
            tenant_id=tenant_b.id,
            email="owner@elpuerto.es",
            password_hash=hash_password("owner456"),
            name="Juan Pérez",
            role="owner",
        )
        db.add(owner_b)
        await db.flush()

        # 6. Manager for Tenant A
        manager_a = User(
            tenant_id=tenant_a.id,
            email="manager@latagliatella.es",
            password_hash=hash_password("manager123"),
            name="Carlos Manager",
            role="manager",
        )
        db.add(manager_a)
        await db.flush()

        # 7. Shifts for Tenant A
        shift_morning = Shift(
            tenant_id=tenant_a.id,
            name="Mañana",
            start_time=time(8, 0),
            end_time=time(16, 0),
            tolerance_min=5,
            is_split=False,
            break_min=30,
            color="#FF6B35",
        )
        shift_afternoon = Shift(
            tenant_id=tenant_a.id,
            name="Tarde",
            start_time=time(16, 0),
            end_time=time(0, 0),
            tolerance_min=5,
            is_split=False,
            break_min=30,
            color="#0F766E",
        )
        db.add(shift_morning)
        db.add(shift_afternoon)
        await db.flush()

        # 8. Employees for Tenant A (with known PINs)
        emp1 = Employee(
            tenant_id=tenant_a.id,
            name="Carlos López",
            dni="12345678A",
            pin_hash=hash_password("1234"),
            pin_hash_fast=compute_pin_hash_fast("1234"),
            nfc_uid="NFC001",
            shift_id=shift_morning.id,
            is_active=True,
        )
        emp2 = Employee(
            tenant_id=tenant_a.id,
            name="Ana Martínez",
            dni="23456789B",
            pin_hash=hash_password("5678"),
            pin_hash_fast=compute_pin_hash_fast("5678"),
            nfc_uid="NFC002",
            shift_id=shift_afternoon.id,
            is_active=True,
        )
        db.add(emp1)
        db.add(emp2)
        await db.flush()

        # 9. Employee for Tenant B (for cross-tenant isolation)
        emp_b1 = Employee(
            tenant_id=tenant_b.id,
            name="Pedro TenantB",
            dni="99999999Z",
            pin_hash=hash_password("9999"),
            pin_hash_fast=compute_pin_hash_fast("9999"),
            shift_id=None,
            is_active=True,
        )
        db.add(emp_b1)
        await db.flush()

        # 10. VacationRequest for Tenant A (pending)
        vac1 = VacationRequest(
            tenant_id=tenant_a.id,
            employee_id=emp1.id,
            type="vacation",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            total_days=5,
            days_count_method="working",
            reason="Vacaciones de verano",
            status="pending",
        )
        db.add(vac1)
        await db.flush()

        # 11. Leave for Tenant A
        leave1 = Leave(
            tenant_id=tenant_a.id,
            employee_id=emp2.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            leave_type="medical",
            type="medical",
            reason="Gripe",
            is_active=True,
        )
        db.add(leave1)
        await db.flush()

        # 12. Holiday for Tenant A
        holiday1 = Holiday(
            tenant_id=tenant_a.id,
            name="Navidad",
            date=date(date.today().year, 12, 25),
            is_recurring=True,
        )
        db.add(holiday1)
        await db.flush()

        await db.commit()

    # Build tokens
    admin_token = create_access_token({
        "sub": str(admin.id),
        "email": admin.email,
        "role": admin.role,
        "tenant_id": None,
    })
    owner_a_token = create_access_token({
        "sub": str(owner_a.id),
        "email": owner_a.email,
        "role": owner_a.role,
        "tenant_id": str(tenant_a.id),
    })
    owner_b_token = create_access_token({
        "sub": str(owner_b.id),
        "email": owner_b.email,
        "role": owner_b.role,
        "tenant_id": str(tenant_b.id),
    })
    manager_a_token = create_access_token({
        "sub": str(manager_a.id),
        "email": manager_a.email,
        "role": manager_a.role,
        "tenant_id": str(tenant_a.id),
    })

    return {
        "admin_id": str(admin.id),
        "admin_token": admin_token,
        "owner_a_id": str(owner_a.id),
        "owner_a_token": owner_a_token,
        "owner_b_id": str(owner_b.id),
        "owner_b_token": owner_b_token,
        "manager_a_token": manager_a_token,
        "tenant_a_id": str(tenant_a.id),
        "tenant_b_id": str(tenant_b.id),
        "emp1_id": str(emp1.id),
        "emp2_id": str(emp2.id),
        "emp_b1_id": str(emp_b1.id),
        "shift_morning_id": str(shift_morning.id),
        "shift_afternoon_id": str(shift_afternoon.id),
        "vac1_id": str(vac1.id),
        "leave1_id": str(leave1.id),
        "holiday1_id": str(holiday1.id),
    }


# ── Override DB dependency ─────────────────────────────────────────────────
@pytest_asyncio.fixture
async def db_session():
    """Provide a clean DB session for direct queries in tests."""
    async with async_session_factory() as session:
        yield session


# ── Async HTTP client ───────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client():
    """Return an async HTTP client wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
