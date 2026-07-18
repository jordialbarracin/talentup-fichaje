"""
TalentUP Fichaje — Seed data script.
Creates: super_admin, example tenant, owner, shifts, employees with PINs.
"""
import asyncio
import os
import sys
from datetime import time

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SQLITE_FALLBACK"] = "true"

from app.database import async_session_factory, init_db, engine
from app.models.tenant import Tenant
from app.models.user import User
from app.models.shift import Shift
from app.models.employee import Employee
from app.auth import hash_password


async def seed():
    print("🌱 Seeding TalentUP Fichaje database...")
    await init_db()

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
        print("  ✓ Super admin created: admin@talentup.es / admin123")

        # 2. Example Tenant
        tenant = Tenant(
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
        db.add(tenant)
        await db.flush()
        print(f"  ✓ Tenant created: {tenant.name} (id: {tenant.id})")

        # 3. Owner
        owner = User(
            tenant_id=tenant.id,
            email="owner@latagliatella.es",
            password_hash=hash_password("owner123"),
            name="María García",
            role="owner",
        )
        db.add(owner)
        print("  ✓ Owner created: owner@latagliatella.es / owner123")

        # 4. Shifts
        shifts_data = [
            Shift(
                tenant_id=tenant.id,
                name="Mañana",
                start_time=time(8, 0),
                end_time=time(16, 0),
                tolerance_min=5,
                is_split=False,
                break_min=30,
                color="#FF6B35",
            ),
            Shift(
                tenant_id=tenant.id,
                name="Tarde",
                start_time=time(16, 0),
                end_time=time(0, 0),
                tolerance_min=5,
                is_split=False,
                break_min=30,
                color="#0F766E",
            ),
            Shift(
                tenant_id=tenant.id,
                name="Partido",
                start_time=time(8, 0),
                end_time=time(22, 0),
                tolerance_min=10,
                is_split=True,
                break_min=120,
                color="#7C3AED",
            ),
        ]
        for s in shifts_data:
            db.add(s)
        await db.flush()
        print(f"  ✓ {len(shifts_data)} shifts created")

        # 5. Employees with PINs
        employees_data = [
            {"name": "Carlos López", "dni": "12345678A", "pin": "1234", "shift_id": shifts_data[0].id},
            {"name": "Ana Martínez", "dni": "23456789B", "pin": "5678", "shift_id": shifts_data[1].id},
            {"name": "David Sánchez", "dni": "34567890C", "pin": "9012", "shift_id": shifts_data[2].id},
            {"name": "Laura Fernández", "dni": "45678901D", "pin": "3456", "shift_id": shifts_data[0].id},
            {"name": "Javier Ruiz", "dni": "56789012E", "pin": "7890", "shift_id": shifts_data[1].id},
            {"name": "Sara Gómez", "dni": "67890123F", "pin": "2345", "shift_id": shifts_data[2].id},
            {"name": "Pedro Díaz", "dni": "78901234G", "pin": "6789", "shift_id": shifts_data[0].id},
            {"name": "Elena Torres", "dni": "89012345H", "pin": "0123", "shift_id": shifts_data[1].id},
            {"name": "Miguel Ángel", "dni": "90123456I", "pin": "4567", "shift_id": shifts_data[2].id},
            {"name": "Carmen Ruiz", "dni": "01234567J", "pin": "8901", "shift_id": shifts_data[0].id},
        ]

        for emp_data in employees_data:
            emp = Employee(
                tenant_id=tenant.id,
                name=emp_data["name"],
                dni=emp_data["dni"],
                pin_hash=hash_password(emp_data["pin"]),
                shift_id=emp_data["shift_id"],
                is_active=True,
            )
            db.add(emp)

        await db.commit()
        print(f"  ✓ {len(employees_data)} employees created with PINs")
        print()
        print("📋 Seed complete!")
        print("  ┌──────────────────────┬──────────────────────────────┐")
        print("  │ Email/User           │ Password/PIN                 │")
        print("  ├──────────────────────┼──────────────────────────────┤")
        print("  │ admin@talentup.es    │ admin123 (super_admin)       │")
        print("  │ owner@latagliatella.es │ owner123 (owner)            │")
        print("  ├──────────────────────┼──────────────────────────────┤")
        for e in employees_data:
            print(f"  │ {e['name']:<20} │ PIN: {e['pin']:<26} │")
        print("  └──────────────────────┴──────────────────────────────┘")


if __name__ == "__main__":
    asyncio.run(seed())
