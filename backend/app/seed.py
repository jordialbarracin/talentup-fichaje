"""
TalentUP Fichaje — Seed data script.
Creates: super_admin, example tenant, owner, shifts, employees with full data,
contracts, holidays, vacation requests, leave, overtime, payroll, notifications, calendar.
"""
import asyncio
import os
import sys
from datetime import date, datetime, time, timedelta, timezone

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SQLITE_FALLBACK"] = "true"

from app.database import async_session_factory, init_db, engine
from app.models.tenant import Tenant
from app.models.user import User
from app.models.shift import Shift
from app.models.employee import Employee
from app.models.contract import Contract
from app.models.holiday import Holiday
from app.models.vacation_request import VacationRequest
from app.models.leave import Leave
from app.models.overtime import Overtime
from app.models.payroll import Payroll
from app.models.notification import Notification
from app.models.work_calendar import WorkCalendar
from app.auth import hash_password


async def seed():
    print("🌱 Seeding TalentUP Fichaje database (v2.0)...")
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
            city="Madrid",
            province="Madrid",
            postal_code="28013",
            phone="+34 912 345 678",
            email="info@latagliatella.es",
            website="https://latagliatella.es",
            convenio="hosteleria",
            ccaa="Madrid",
            locality="Madrid",
            sector="restaurante",
            tolerancia_min=5,
            default_grace_period=15,
            auto_detect_incidents=True,
            allow_offline_clock=True,
            vacation_days_per_year=30,
            vacation_requires_approval=True,
            min_vacation_days_before=15,
            payroll_day=30,
            irpf_default=12.0,
            ss_employee_percent=6.35,
            ss_company_percent=29.90,
            plan="premium",
            max_employees=50,
            setup_completed=True,
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

        # 4. Shifts (ampliados)
        shifts_data = [
            Shift(
                tenant_id=tenant.id,
                name="Mañana",
                code="M",
                shift_type="morning",
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_min=30,
                tolerance_min=5,
                grace_period_min=15,
                is_split=False,
                is_night=False,
                plus_nocturnidad=0,
                plus_festividad=25,
                is_rotativo=False,
                color="#FF6B35",
                sort_order=1,
            ),
            Shift(
                tenant_id=tenant.id,
                name="Tarde",
                code="T",
                shift_type="afternoon",
                start_time=time(15, 0),
                end_time=time(23, 0),
                break_min=30,
                tolerance_min=5,
                grace_period_min=15,
                is_split=False,
                is_night=False,
                plus_nocturnidad=0,
                plus_festividad=25,
                is_rotativo=False,
                color="#0F766E",
                sort_order=2,
            ),
            Shift(
                tenant_id=tenant.id,
                name="Noche",
                code="N",
                shift_type="night",
                start_time=time(23, 0),
                end_time=time(7, 0),
                break_min=30,
                tolerance_min=10,
                grace_period_min=15,
                is_split=False,
                is_night=True,
                plus_nocturnidad=25,
                plus_festividad=25,
                is_rotativo=False,
                color="#1E3A5F",
                sort_order=3,
            ),
            Shift(
                tenant_id=tenant.id,
                name="Partido",
                code="P",
                shift_type="split",
                start_time=time(10, 0),
                end_time=time(23, 0),
                break_start=time(16, 0),
                break_end=time(20, 0),
                break_min=120,
                tolerance_min=10,
                grace_period_min=15,
                is_split=True,
                is_night=False,
                plus_nocturnidad=0,
                plus_festividad=25,
                is_rotativo=False,
                color="#7C3AED",
                sort_order=4,
            ),
            Shift(
                tenant_id=tenant.id,
                name="Rotativo",
                code="R",
                shift_type="rotating",
                start_time=time(7, 0),
                end_time=time(15, 0),
                break_min=30,
                tolerance_min=5,
                grace_period_min=15,
                is_split=False,
                is_night=False,
                plus_nocturnidad=0,
                plus_festividad=25,
                is_rotativo=True,
                color="#F59E0B",
                sort_order=5,
            ),
        ]
        for s in shifts_data:
            db.add(s)
        await db.flush()
        print(f"  ✓ {len(shifts_data)} shifts created (ampliados)")

        # 5. Employees with full data
        employees_data = [
            {
                "name": "Carlos", "last_name": "López García",
                "dni": "12345678A", "nie": None, "numero_ss": "28/12345678/00",
                "nationality": "Española", "birth_date": date(1990, 3, 15),
                "phone": "+34 612 345 678", "email": "carlos.lopez@email.com",
                "address": "Calle Gran Vía 10, Madrid",
                "categoria_profesional": "COC-03", "tipo_contrato": "IND",
                "fecha_alta": date(2023, 1, 15), "tipo_jornada": "completa",
                "horas_semanales": 40, "grupo_cotizacion": "10", "base_cotizacion": 1500,
                "coste_hora": 12.50, "iban": "ES91 2100 0418 4502 0005 1332",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "1234", "shift_id": shifts_data[0].id,
                "nfc_uid": "04:A1:B2:C3:D4:E5",
                "food_handling_cert": True, "uniform_size": "M",
            },
            {
                "name": "Ana", "last_name": "Martínez Ruiz",
                "dni": "23456789B", "nie": None, "numero_ss": "28/23456789/00",
                "nationality": "Española", "birth_date": date(1995, 7, 22),
                "phone": "+34 623 456 789", "email": "ana.martinez@email.com",
                "address": "Calle Alcalá 25, Madrid",
                "categoria_profesional": "SAL-03", "tipo_contrato": "IND",
                "fecha_alta": date(2023, 3, 1), "tipo_jornada": "completa",
                "horas_semanales": 40, "grupo_cotizacion": "10", "base_cotizacion": 1400,
                "coste_hora": 11.67, "iban": "ES91 2100 0418 4502 0005 1333",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "5678", "shift_id": shifts_data[1].id,
                "nfc_uid": "04:A1:B2:C3:D4:E6",
                "food_handling_cert": True, "uniform_size": "S",
            },
            {
                "name": "David", "last_name": "Sánchez Pérez",
                "dni": "34567890C", "nie": None, "numero_ss": "28/34567890/00",
                "nationality": "Española", "birth_date": date(1988, 11, 5),
                "phone": "+34 634 567 890", "email": "david.sanchez@email.com",
                "address": "Calle Serrano 50, Madrid",
                "categoria_profesional": "COC-01", "tipo_contrato": "IND",
                "fecha_alta": date(2022, 6, 1), "tipo_jornada": "completa",
                "horas_semanales": 40, "grupo_cotizacion": "9", "base_cotizacion": 2000,
                "coste_hora": 16.67, "iban": "ES91 2100 0418 4502 0005 1334",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "9012", "shift_id": shifts_data[2].id,
                "nfc_uid": "04:A1:B2:C3:D4:E7",
                "food_handling_cert": True, "uniform_size": "L",
            },
            {
                "name": "Laura", "last_name": "Fernández López",
                "dni": "45678901D", "nie": None, "numero_ss": "28/45678901/00",
                "nationality": "Española", "birth_date": date(1992, 2, 14),
                "phone": "+34 645 678 901", "email": "laura.fernandez@email.com",
                "address": "Calle Velázquez 15, Madrid",
                "categoria_profesional": "SAL-01", "tipo_contrato": "IND",
                "fecha_alta": date(2023, 9, 1), "tipo_jornada": "completa",
                "horas_semanales": 40, "grupo_cotizacion": "9", "base_cotizacion": 1800,
                "coste_hora": 15.00, "iban": "ES91 2100 0418 4502 0005 1335",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "3456", "shift_id": shifts_data[0].id,
                "food_handling_cert": True, "uniform_size": "M",
            },
            {
                "name": "Javier", "last_name": "Ruiz Gómez",
                "dni": "56789012E", "nie": None, "numero_ss": "28/56789012/00",
                "nationality": "Española", "birth_date": date(1993, 9, 30),
                "phone": "+34 656 789 012", "email": "javier.ruiz@email.com",
                "address": "Calle Goya 30, Madrid",
                "categoria_profesional": "BAR-02", "tipo_contrato": "IND",
                "fecha_alta": date(2024, 1, 10), "tipo_jornada": "completa",
                "horas_semanales": 40, "grupo_cotizacion": "10", "base_cotizacion": 1300,
                "coste_hora": 10.83, "iban": "ES91 2100 0418 4502 0005 1336",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "7890", "shift_id": shifts_data[1].id,
                "food_handling_cert": True, "uniform_size": "XL",
            },
            {
                "name": "Sara", "last_name": "Gómez Díaz",
                "dni": "67890123F", "nie": None, "numero_ss": "28/67890123/00",
                "nationality": "Española", "birth_date": date(1997, 5, 18),
                "phone": "+34 667 890 123", "email": "sara.gomez@email.com",
                "address": "Calle Fuencarral 45, Madrid",
                "categoria_profesional": "COC-04", "tipo_contrato": "TEM-OC",
                "fecha_alta": date(2024, 6, 1), "tipo_jornada": "parcial",
                "horas_semanales": 25, "grupo_cotizacion": "10", "base_cotizacion": 800,
                "coste_hora": 10.00, "iban": "ES91 2100 0418 4502 0005 1337",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "2345", "shift_id": shifts_data[2].id,
                "food_handling_cert": True, "uniform_size": "S",
            },
            {
                "name": "Pedro", "last_name": "Díaz Martín",
                "dni": "78901234G", "nie": None, "numero_ss": "28/78901234/00",
                "nationality": "Española", "birth_date": date(1985, 12, 1),
                "phone": "+34 678 901 234", "email": "pedro.diaz@email.com",
                "address": "Calle Princesa 20, Madrid",
                "categoria_profesional": "ADM-01", "tipo_contrato": "IND",
                "fecha_alta": date(2022, 1, 1), "tipo_jornada": "completa",
                "horas_semanales": 40, "grupo_cotizacion": "7", "base_cotizacion": 2500,
                "coste_hora": 20.83, "iban": "ES91 2100 0418 4502 0005 1338",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "6789", "shift_id": shifts_data[0].id,
                "food_handling_cert": False, "uniform_size": "L",
            },
            {
                "name": "Elena", "last_name": "Torres Navarro",
                "dni": "89012345H", "nie": None, "numero_ss": "28/89012345/00",
                "nationality": "Española", "birth_date": date(1991, 8, 10),
                "phone": "+34 689 012 345", "email": "elena.torres@email.com",
                "address": "Calle Castellana 100, Madrid",
                "categoria_profesional": "ADM-03", "tipo_contrato": "IND",
                "fecha_alta": date(2023, 11, 15), "tipo_jornada": "completa",
                "horas_semanales": 40, "grupo_cotizacion": "10", "base_cotizacion": 1600,
                "coste_hora": 13.33, "iban": "ES91 2100 0418 4502 0005 1339",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "0123", "shift_id": shifts_data[1].id,
                "food_handling_cert": False, "uniform_size": "M",
            },
            {
                "name": "Miguel", "last_name": "Ángel Romero",
                "dni": "90123456I", "nie": None, "numero_ss": "28/90123456/00",
                "nationality": "Española", "birth_date": date(1994, 4, 25),
                "phone": "+34 690 123 456", "email": "miguel.angel@email.com",
                "address": "Calle Atocha 5, Madrid",
                "categoria_profesional": "MNT-01", "tipo_contrato": "IND",
                "fecha_alta": date(2023, 5, 1), "tipo_jornada": "completa",
                "horas_semanales": 40, "grupo_cotizacion": "10", "base_cotizacion": 1400,
                "coste_hora": 11.67, "iban": "ES91 2100 0418 4502 0005 1340",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "4567", "shift_id": shifts_data[2].id,
                "food_handling_cert": False, "uniform_size": "XL",
            },
            {
                "name": "Carmen", "last_name": "Ruiz López",
                "dni": "01234567J", "nie": None, "numero_ss": "28/01234567/00",
                "nationality": "Española", "birth_date": date(1996, 6, 8),
                "phone": "+34 601 234 567", "email": "carmen.ruiz@email.com",
                "address": "Calle Hortaleza 12, Madrid",
                "categoria_profesional": "APR-01", "tipo_contrato": "TEM-FOR",
                "fecha_alta": date(2025, 1, 15), "tipo_jornada": "parcial",
                "horas_semanales": 20, "grupo_cotizacion": "10", "base_cotizacion": 500,
                "coste_hora": 7.50, "iban": "ES91 2100 0418 4502 0005 1341",
                "saldo_vacaciones": 30, "saldo_banco_horas": 0, "horas_extra_pendientes": 0,
                "pin": "8901", "shift_id": shifts_data[0].id,
                "food_handling_cert": True, "uniform_size": "M",
            },
        ]

        created_employees = []
        for emp_data in employees_data:
            emp = Employee(
                tenant_id=tenant.id,
                name=emp_data["name"],
                last_name=emp_data["last_name"],
                full_name=f"{emp_data['name']} {emp_data['last_name']}",
                dni=emp_data["dni"],
                nie=emp_data.get("nie"),
                numero_ss=emp_data["numero_ss"],
                nationality=emp_data["nationality"],
                birth_date=emp_data["birth_date"],
                phone=emp_data["phone"],
                email=emp_data["email"],
                address=emp_data["address"],
                categoria_profesional=emp_data["categoria_profesional"],
                tipo_contrato=emp_data["tipo_contrato"],
                fecha_alta=emp_data["fecha_alta"],
                tipo_jornada=emp_data["tipo_jornada"],
                horas_semanales=emp_data["horas_semanales"],
                grupo_cotizacion=emp_data["grupo_cotizacion"],
                base_cotizacion=emp_data["base_cotizacion"],
                coste_hora=emp_data["coste_hora"],
                iban=emp_data["iban"],
                saldo_vacaciones=emp_data["saldo_vacaciones"],
                saldo_banco_horas=emp_data["saldo_banco_horas"],
                horas_extra_pendientes=emp_data["horas_extra_pendientes"],
                pin_hash=hash_password(emp_data["pin"]),
                shift_id=emp_data["shift_id"],
                nfc_uid=emp_data.get("nfc_uid"),
                food_handling_cert=emp_data["food_handling_cert"],
                uniform_size=emp_data["uniform_size"],
                estado="activo",
                is_active=True,
                employee_code=f"EMP-{len(created_employees)+1:03d}",
            )
            db.add(emp)
            created_employees.append(emp)

        await db.flush()
        print(f"  ✓ {len(created_employees)} employees created with full data")

        # 6. Contracts (histórico de contratos)
        contracts_data = [
            Contract(
                tenant_id=tenant.id, employee_id=created_employees[0].id,
                contract_type="IND", category="COC-03",
                start_date=date(2023, 1, 15), is_indefinite=True,
                work_day_type="completa", weekly_hours=40,
                salary_base=1500, status="active",
            ),
            Contract(
                tenant_id=tenant.id, employee_id=created_employees[1].id,
                contract_type="IND", category="SAL-03",
                start_date=date(2023, 3, 1), is_indefinite=True,
                work_day_type="completa", weekly_hours=40,
                salary_base=1400, status="active",
            ),
            Contract(
                tenant_id=tenant.id, employee_id=created_employees[2].id,
                contract_type="IND", category="COC-01",
                start_date=date(2022, 6, 1), is_indefinite=True,
                work_day_type="completa", weekly_hours=40,
                salary_base=2000, status="active",
            ),
            Contract(
                tenant_id=tenant.id, employee_id=created_employees[5].id,
                contract_type="TEM-OC", category="COC-04",
                start_date=date(2024, 6, 1), end_date=date(2025, 12, 31),
                is_indefinite=False, duration_days=365,
                work_day_type="parcial", weekly_hours=25,
                salary_base=800, status="active",
            ),
            Contract(
                tenant_id=tenant.id, employee_id=created_employees[9].id,
                contract_type="TEM-FOR", category="APR-01",
                start_date=date(2025, 1, 15), end_date=date(2026, 1, 14),
                is_indefinite=False, duration_days=365,
                work_day_type="parcial", weekly_hours=20,
                salary_base=500, status="active",
            ),
        ]
        for c in contracts_data:
            db.add(c)
        await db.flush()
        print(f"  ✓ {len(contracts_data)} contracts created")

        # 7. Holidays 2026 (festivos nacionales + Madrid)
        holidays_2026 = [
            # Nacionales
            Holiday(tenant_id=tenant.id, date=date(2026, 1, 1), name="Año Nuevo", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 1, 6), name="Epifanía del Señor (Reyes)", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 4, 3), name="Viernes Santo", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 5, 1), name="Fiesta del Trabajo", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 8, 15), name="Asunción de la Virgen", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 10, 12), name="Fiesta Nacional de España", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 11, 1), name="Todos los Santos", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 12, 6), name="Día de la Constitución", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 12, 8), name="Inmaculada Concepción", type="national", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 12, 25), name="Navidad", type="national", year=2026),
            # Madrid (autonómicos)
            Holiday(tenant_id=tenant.id, date=date(2026, 5, 2), name="Fiesta de la Comunidad de Madrid", type="regional", region="Madrid", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 6, 3), name="Corpus Christi", type="regional", region="Madrid", year=2026),
            # Locales (Madrid capital)
            Holiday(tenant_id=tenant.id, date=date(2026, 5, 15), name="San Isidro Labrador", type="local", region="Madrid", locality="Madrid", year=2026),
            Holiday(tenant_id=tenant.id, date=date(2026, 11, 9), name="La Almudena", type="local", region="Madrid", locality="Madrid", year=2026),
        ]
        for h in holidays_2026:
            db.add(h)
        await db.flush()
        print(f"  ✓ {len(holidays_2026)} holidays created for 2026")

        # 8. Vacation requests
        vac_requests = [
            VacationRequest(
                tenant_id=tenant.id, employee_id=created_employees[0].id,
                type="vacation", start_date=date(2026, 7, 21), end_date=date(2026, 7, 28),
                total_days=6, days_count_method="working",
                reason="Vacaciones de verano", status="approved",
                approved_by=owner.id, approved_at=datetime.now(timezone.utc),
            ),
            VacationRequest(
                tenant_id=tenant.id, employee_id=created_employees[1].id,
                type="vacation", start_date=date(2026, 8, 1), end_date=date(2026, 8, 15),
                total_days=11, days_count_method="working",
                reason="Vacaciones familiares", status="pending",
            ),
            VacationRequest(
                tenant_id=tenant.id, employee_id=created_employees[3].id,
                type="vacation", start_date=date(2026, 9, 1), end_date=date(2026, 9, 10),
                total_days=8, days_count_method="working",
                reason="Viaje", status="pending",
            ),
            VacationRequest(
                tenant_id=tenant.id, employee_id=created_employees[6].id,
                type="personal_leave", start_date=date(2026, 7, 5), end_date=date(2026, 7, 5),
                total_days=1, days_count_method="working",
                reason="Asunto personal", status="approved",
                approved_by=owner.id, approved_at=datetime.now(timezone.utc),
            ),
        ]
        for v in vac_requests:
            db.add(v)
        await db.flush()
        print(f"  ✓ {len(vac_requests)} vacation requests created")

        # 9. Leave (baja IT de ejemplo)
        leave_example = Leave(
            tenant_id=tenant.id, employee_id=created_employees[4].id,
            leave_type="EC", start_date=date(2026, 6, 15),
            expected_end_date=date(2026, 7, 15), total_days=30,
            diagnosis_code="J06.9", medical_center="Hospital Clínico San Carlos",
            doctor_name="Dr. Martínez", part_number="PART-2026-001",
            mutua="FREMAP", is_work_accident=False,
            is_professional_illness=False, has_leave_report=True,
            status="active", created_by=owner.id,
        )
        db.add(leave_example)
        await db.flush()
        print("  ✓ 1 leave (IT) created")

        # 10. Overtime (horas extra de ejemplo)
        overtime_data = [
            Overtime(
                tenant_id=tenant.id, employee_id=created_employees[0].id,
                date=date(2026, 7, 1), overtime_type="structural",
                total_minutes=120, hourly_rate_multiplier=1.75,
                hourly_rate=12.50, overtime_amount=43.75,
                compensation_type="pending", source="auto",
            ),
            Overtime(
                tenant_id=tenant.id, employee_id=created_employees[2].id,
                date=date(2026, 7, 2), overtime_type="structural",
                total_minutes=90, hourly_rate_multiplier=1.75,
                hourly_rate=16.67, overtime_amount=43.76,
                compensation_type="pending", source="auto",
            ),
        ]
        for o in overtime_data:
            db.add(o)
        await db.flush()
        print(f"  ✓ {len(overtime_data)} overtime records created")

        # 11. Payroll (nómina de ejemplo para julio 2026)
        for emp in created_employees[:5]:
            payroll = Payroll(
                tenant_id=tenant.id, employee_id=emp.id,
                year=2026, month=7, period_label="Julio 2026",
                contract_type=emp.tipo_contrato,
                professional_category=emp.categoria_profesional,
                work_day_type=emp.tipo_jornada,
                weekly_hours=emp.horas_semanales,
                scheduled_hours=160, worked_hours=168,
                worked_days=21, absent_days=0,
                base_salary=float(emp.base_cotizacion or 0),
                overtime_total=2, overtime_amount=43.75,
                gross_total=float(emp.base_cotizacion or 0) + 43.75,
                ss_deduction=float(emp.base_cotizacion or 0) * 0.0635,
                irpf_deduction=float(emp.base_cotizacion or 0) * 0.12,
                status="draft",
            )
            payroll.net_total = payroll.gross_total - payroll.ss_deduction - payroll.irpf_deduction
            db.add(payroll)
        await db.flush()
        print("  ✓ 5 payroll records created for July 2026")

        # 12. Notifications
        notifications_data = [
            Notification(
                tenant_id=tenant.id, recipient_type="employee",
                employee_id=created_employees[0].id,
                type="vacation_approved", title="Vacaciones aprobadas",
                message="Tus vacaciones del 21 al 28 de julio han sido aprobadas.",
                priority="normal", category="vacation",
                sent_via="in_app", sent_at=datetime.now(timezone.utc),
            ),
            Notification(
                tenant_id=tenant.id, recipient_type="manager",
                type="vacation_request", title="Nueva solicitud de vacaciones",
                message="Ana Martínez ha solicitado vacaciones del 1 al 15 de agosto.",
                priority="normal", category="vacation",
                sent_via="in_app", sent_at=datetime.now(timezone.utc),
            ),
            Notification(
                tenant_id=tenant.id, recipient_type="employee",
                employee_id=created_employees[4].id,
                type="leave_start", title="Inicio de baja registrado",
                message="Se ha registrado tu baja médica desde el 15 de junio.",
                priority="high", category="leave",
                sent_via="in_app", sent_at=datetime.now(timezone.utc),
            ),
        ]
        for n in notifications_data:
            db.add(n)
        await db.flush()
        print(f"  ✓ {len(notifications_data)} notifications created")

        # 13. Work Calendar 2026 (generate from holidays)
        from datetime import date as dt_date, timedelta as td
        start = dt_date(2026, 1, 1)
        end = dt_date(2026, 12, 31)
        current = start
        holiday_dates = {h.date: h for h in holidays_2026}
        calendar_days = []
        while current <= end:
            is_weekend = current.weekday() >= 5
            is_holiday = current in holiday_dates
            holiday = holiday_dates.get(current)
            day = WorkCalendar(
                tenant_id=tenant.id, year=2026, date=current,
                day_type="holiday" if is_holiday else ("weekend" if is_weekend else "working"),
                is_working_day=not is_weekend and not is_holiday,
                is_holiday=is_holiday, is_weekend=is_weekend,
                holiday_id=holiday.id if holiday else None,
                holiday_name=holiday.name if holiday else None,
            )
            calendar_days.append(day)
            current += td(days=1)
        for d in calendar_days:
            db.add(d)
        await db.flush()
        print(f"  ✓ {len(calendar_days)} work calendar days created for 2026")

        await db.commit()
        print()
        print("📋 Seed v2.0 complete!")
        print("  ┌──────────────────────┬──────────────────────────────┐")
        print("  │ Email/User           │ Password/PIN                 │")
        print("  ├──────────────────────┼──────────────────────────────┤")
        print("  │ admin@talentup.es    │ admin123 (super_admin)       │")
        print("  │ owner@latagliatella.es │ owner123 (owner)            │")
        print("  ├──────────────────────┼──────────────────────────────┤")
        for e in employees_data:
            print(f"  │ {e['name']+' '+e['last_name']:<20} │ PIN: {e['pin']:<26} │")
        print("  └──────────────────────┴──────────────────────────────┘")
        print()
        print("  📊 New tables seeded:")
        print("     - contracts, holidays, vacation_requests, leave")
        print("     - overtime, payroll, notifications, work_calendar")
        print("     - Employees with 34 fields each")
        print("     - Shifts with plus_nocturnidad, plus_festividad, is_rotativo")
        print("     - Tenants with convenio/vacaciones/billing config")


if __name__ == "__main__":
    asyncio.run(seed())
