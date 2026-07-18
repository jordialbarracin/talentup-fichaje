"""
TalentUP Fichaje — Comprehensive E2E API tests.
Covers: auth, employees, clock, shifts, vacations, leave, holidays, reports, security, incidents.
"""
import pytest
from datetime import datetime, timezone, date, timedelta


# ═══════════════════════════════════════════════════════════════════════════
# 1. AUTH
# ═══════════════════════════════════════════════════════════════════════════

class TestAuth:
    """POST /api/auth/login and GET /api/auth/me"""

    async def test_login_correct(self, client, seed_data):
        """Login with correct credentials → 200 + token"""
        resp = await client.post("/api/auth/login", json={
            "email": "owner@latagliatella.es",
            "password": "owner123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "owner@latagliatella.es"
        assert body["user"]["role"] == "owner"

    async def test_login_incorrect(self, client, seed_data):
        """Login with wrong password → 401"""
        resp = await client.post("/api/auth/login", json={
            "email": "owner@latagliatella.es",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert "detail" in resp.json()

    async def test_me_with_token(self, client, seed_data):
        """GET /api/auth/me with valid token → 200"""
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "owner@latagliatella.es"
        assert body["role"] == "owner"

    async def test_me_without_token(self, client, seed_data):
        """GET /api/auth/me without token → 401"""
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401
        assert "detail" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# 2. EMPLOYEES
# ═══════════════════════════════════════════════════════════════════════════

class TestEmployees:
    """CRUD /api/employees with tenant isolation"""

    async def test_list_employees(self, client, seed_data):
        """GET /api/employees → list"""
        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 2
        names = [e["name"] for e in body]
        assert "Carlos López" in names
        assert "Ana Martínez" in names

    async def test_create_employee(self, client, seed_data):
        """POST /api/employees → crear"""
        resp = await client.post(
            "/api/employees",
            json={
                "name": "Nuevo Empleado",
                "dni": "11111111H",
                "pin": "4321",
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Nuevo Empleado"
        assert body["dni"] == "11111111H"
        assert body["is_active"] is True
        assert "id" in body
        assert body["tenant_id"] == seed_data["tenant_a_id"]
        assert "pin" not in body
        assert "pin_hash" not in body

    async def test_update_employee(self, client, seed_data):
        """PUT /api/employees/{id} → actualizar"""
        resp = await client.put(
            f"/api/employees/{seed_data['emp1_id']}",
            json={"name": "Carlos Actualizado", "dni": "87654321Z"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Carlos Actualizado"
        assert body["dni"] == "87654321Z"

    async def test_delete_employee(self, client, seed_data):
        """DELETE /api/employees/{id} → eliminar"""
        resp = await client.delete(
            f"/api/employees/{seed_data['emp1_id']}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 204

        # Verify it's gone
        resp2 = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        ids = [e["id"] for e in resp2.json()]
        assert seed_data["emp1_id"] not in ids

    async def test_list_employees_without_token(self, client, seed_data):
        """GET /api/employees sin token → 401"""
        resp = await client.get("/api/employees")
        assert resp.status_code == 401

    async def test_cross_tenant_isolation(self, client, seed_data):
        """Owner B no ve empleados de tenant A"""
        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {seed_data['owner_b_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["name"] == "Pedro TenantB"


# ═══════════════════════════════════════════════════════════════════════════
# 3. CLOCK (FICHAJE)
# ═══════════════════════════════════════════════════════════════════════════

class TestClock:
    """POST /api/clock (public, PIN-based) and GET /api/clock/today"""

    async def test_clock_in_valid_pin(self, client, seed_data):
        """POST /api/clock PIN válido type 'in' → 201"""
        resp = await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["ok"] is True
        assert "Carlos López" in body["message"]
        assert body["clock"]["type"] == "in"
        assert body["clock"]["employee_id"] == seed_data["emp1_id"]

    async def test_clock_out_after_in(self, client, seed_data):
        """POST /api/clock PIN válido type 'out' (después de in) → 201"""
        # First clock in
        resp_in = await client.post("/api/clock", json={
            "pin": "5678",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp_in.status_code == 201

        # Then clock out
        resp_out = await client.post("/api/clock", json={
            "pin": "5678",
            "type": "out",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp_out.status_code == 201
        body = resp_out.json()
        assert body["ok"] is True
        assert body["clock"]["type"] == "out"

    async def test_clock_invalid_pin(self, client, seed_data):
        """POST /api/clock PIN inválido → 401"""
        resp = await client.post("/api/clock", json={
            "pin": "0000",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp.status_code == 401
        assert "PIN incorrecto" in resp.json()["detail"]

    async def test_clock_invalid_type(self, client, seed_data):
        """POST /api/clock type inválido → 422"""
        resp = await client.post("/api/clock", json={
            "pin": "1234",
            "type": "invalid_type_xyz",
            "tenant_id": seed_data["tenant_a_id"],
        })
        # Pydantic Literal validation returns 422
        assert resp.status_code == 422

    async def test_clock_missing_tenant_id(self, client, seed_data):
        """POST /api/clock sin tenant_id → 400"""
        resp = await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
        })
        assert resp.status_code == 400
        assert "tenant_id es requerido" in resp.json()["detail"]

    async def test_clock_today(self, client, seed_data):
        """GET /api/clock/today → fichajes de hoy"""
        # Create a clock-in first
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })

        resp = await client.get(
            "/api/clock/today",
            headers={"Authorization": f"Bearer {seed_data['manager_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        assert body[0]["type"] == "in"


# ═══════════════════════════════════════════════════════════════════════════
# 4. SHIFTS
# ═══════════════════════════════════════════════════════════════════════════

class TestShifts:
    """CRUD /api/shifts"""

    async def test_list_shifts(self, client, seed_data):
        """GET /api/shifts → lista"""
        resp = await client.get(
            "/api/shifts",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 2
        names = [s["name"] for s in body]
        assert "Mañana" in names
        assert "Tarde" in names

    async def test_create_shift(self, client, seed_data):
        """POST /api/shifts → crear"""
        resp = await client.post(
            "/api/shifts",
            json={
                "name": "Noche",
                "start_time": "22:00",
                "end_time": "06:00",
                "tolerance_min": 10,
                "is_split": False,
                "break_min": 30,
                "color": "#1E3A5F",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Noche"
        assert body["start_time"] == "22:00"
        assert body["end_time"] == "06:00"
        assert body["tolerance_min"] == 10
        assert "id" in body

    async def test_update_shift(self, client, seed_data):
        """PUT /api/shifts/{id} → actualizar"""
        resp = await client.put(
            f"/api/shifts/{seed_data['shift_morning_id']}",
            json={"name": "Mañana Actualizado", "tolerance_min": 10},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Mañana Actualizado"
        assert body["tolerance_min"] == 10

    async def test_delete_shift(self, client, seed_data):
        """DELETE /api/shifts/{id} → eliminar"""
        # Create a shift to delete (don't delete seeded ones that employees reference)
        resp = await client.post(
            "/api/shifts",
            json={
                "name": "Temporal",
                "start_time": "06:00",
                "end_time": "14:00",
                "tolerance_min": 5,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        shift_id = resp.json()["id"]

        resp_del = await client.delete(
            f"/api/shifts/{shift_id}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp_del.status_code == 204

    async def test_create_shift_invalid_hhmm(self, client, seed_data):
        """POST /api/shifts formato HH:MM inválido → 400"""
        resp = await client.post(
            "/api/shifts",
            json={
                "name": "Malo",
                "start_time": "25:00",
                "end_time": "08:00",
                "tolerance_min": 5,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 400
        assert "Formato inválido" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════
# 5. VACATIONS
# ═══════════════════════════════════════════════════════════════════════════

class TestVacations:
    """CRUD /api/vacations"""

    async def test_list_vacations(self, client, seed_data):
        """GET /api/vacations → lista"""
        resp = await client.get(
            "/api/vacations",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        assert body[0]["status"] == "pending"

    async def test_create_vacation(self, client, seed_data):
        """POST /api/vacations → solicitar vacaciones"""
        future = (date.today() + timedelta(days=60)).isoformat()
        future_end = (date.today() + timedelta(days=65)).isoformat()
        resp = await client.post(
            "/api/vacations",
            json={
                "employee_id": seed_data["emp1_id"],
                "type": "vacation",
                "start_date": future,
                "end_date": future_end,
                "total_days": 5,
                "days_count_method": "working",
                "reason": "Vacaciones familiares",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "pending"
        assert body["employee_id"] == seed_data["emp1_id"]
        assert body["start_date"] == future

    async def test_approve_vacation(self, client, seed_data):
        """POST /api/vacations/{id}/approve → aprobar"""
        resp = await client.post(
            f"/api/vacations/{seed_data['vac1_id']}/approve",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "approved"
        assert body["approved_by"] is not None

    async def test_reject_vacation(self, client, seed_data):
        """POST /api/vacations/{id}/reject → rechazar"""
        # Create a new pending vacation first
        future = (date.today() + timedelta(days=90)).isoformat()
        future_end = (date.today() + timedelta(days=95)).isoformat()
        resp = await client.post(
            "/api/vacations",
            json={
                "employee_id": seed_data["emp1_id"],
                "type": "vacation",
                "start_date": future,
                "end_date": future_end,
                "total_days": 5,
                "days_count_method": "working",
                "reason": "Para rechazar",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        vac_id = resp.json()["id"]

        resp_rej = await client.post(
            f"/api/vacations/{vac_id}/reject",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp_rej.status_code == 200
        body = resp_rej.json()
        assert body["status"] == "rejected"

    async def test_list_vacations_without_token(self, client, seed_data):
        """GET /api/vacations sin token → 401"""
        resp = await client.get("/api/vacations")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 6. LEAVE / BAJAS
# ═══════════════════════════════════════════════════════════════════════════

class TestLeave:
    """CRUD /api/leave"""

    async def test_list_leaves(self, client, seed_data):
        """GET /api/leave → lista"""
        resp = await client.get(
            "/api/leave",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        # The leave model uses 'type' field in to_dict
        assert body[0]["type"] == "medical"

    async def test_create_leave(self, client, seed_data):
        """POST /api/leave → registrar baja"""
        today_str = date.today().isoformat()
        end_str = (date.today() + timedelta(days=10)).isoformat()
        resp = await client.post(
            "/api/leave",
            json={
                "employee_id": seed_data["emp1_id"],
                "leave_type": "medical",
                "start_date": today_str,
                "end_date": end_str,
                "total_days": 10,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["type"] == "medical"
        assert body["employee_id"] == seed_data["emp1_id"]

    async def test_update_leave(self, client, seed_data):
        """PUT /api/leave/{id} → actualizar"""
        new_end = (date.today() + timedelta(days=15)).isoformat()
        resp = await client.put(
            f"/api/leave/{seed_data['leave1_id']}",
            json={"end_date": new_end, "total_days": 15},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["end_date"] == new_end

    async def test_list_leaves_without_token(self, client, seed_data):
        """GET /api/leave sin token → 401"""
        resp = await client.get("/api/leave")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 7. HOLIDAYS
# ═══════════════════════════════════════════════════════════════════════════

class TestHolidays:
    """CRUD /api/holidays"""

    async def test_list_holidays(self, client, seed_data):
        """GET /api/holidays → lista"""
        resp = await client.get(
            "/api/holidays",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        assert body[0]["name"] == "Navidad"

    async def test_create_holiday(self, client, seed_data):
        """POST /api/holidays → crear"""
        resp = await client.post(
            "/api/holidays",
            json={
                "name": "Año Nuevo",
                "date": f"{date.today().year}-01-01",
                "type": "national",
                "year": date.today().year,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Año Nuevo"

    async def test_delete_holiday(self, client, seed_data):
        """DELETE /api/holidays/{id} → eliminar"""
        resp = await client.delete(
            f"/api/holidays/{seed_data['holiday1_id']}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 204

        # Verify it's gone
        resp2 = await client.get(
            "/api/holidays",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        ids = [h["id"] for h in resp2.json()]
        assert seed_data["holiday1_id"] not in ids


# ═══════════════════════════════════════════════════════════════════════════
# 8. REPORTS
# ═══════════════════════════════════════════════════════════════════════════

class TestReports:
    """GET /api/reports/hours, /api/reports/incidents, /api/reports/export"""

    async def test_reports_hours(self, client, seed_data):
        """GET /api/reports/hours → horas por empleado"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Create a clock-in/out pair
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "out",
            "tenant_id": seed_data["tenant_a_id"],
        })

        resp = await client.get(
            f"/api/reports/hours?date_from={today}&date_to={today}",
            headers={"Authorization": f"Bearer {seed_data['manager_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["date_from"] == today
        assert body["date_to"] == today
        assert "employees" in body
        carlos = [e for e in body["employees"] if e["employee_name"] == "Carlos López"]
        assert len(carlos) == 1
        assert carlos[0]["total_hours"] > 0

    async def test_reports_incidents(self, client, seed_data):
        """GET /api/reports/incidents → incidencias"""
        resp = await client.get(
            "/api/reports/incidents",
            headers={"Authorization": f"Bearer {seed_data['manager_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body

    async def test_reports_export_pdf(self, client, seed_data):
        """GET /api/reports/export?format=pdf → PDF binario"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Create clock data
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "out",
            "tenant_id": seed_data["tenant_a_id"],
        })

        resp = await client.get(
            f"/api/reports/export?format=pdf&date_from={today}&date_to={today}",
            headers={"Authorization": f"Bearer {seed_data['manager_a_token']}"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert "Content-Disposition" in resp.headers
        assert len(resp.content) > 100

    async def test_reports_export_excel(self, client, seed_data):
        """GET /api/reports/export?format=excel → Excel binario"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Create clock data
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "out",
            "tenant_id": seed_data["tenant_a_id"],
        })

        resp = await client.get(
            f"/api/reports/export?format=excel&date_from={today}&date_to={today}",
            headers={"Authorization": f"Bearer {seed_data['manager_a_token']}"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert len(resp.content) > 100


# ═══════════════════════════════════════════════════════════════════════════
# 9. SECURITY
# ═══════════════════════════════════════════════════════════════════════════

class TestSecurity:
    """Rate limiting, PIN blocking, token expiry, cross-tenant"""

    async def test_rate_limiting_clock(self, client, seed_data):
        """11 fichajes en 1 minuto → 429"""
        responses = []
        for i in range(12):
            resp = await client.post("/api/clock", json={
                "pin": "1234",
                "type": "in",
                "tenant_id": seed_data["tenant_a_id"],
            })
            responses.append(resp.status_code)

        # At least one should be 429
        rate_limited = [s for s in responses if s == 429]
        assert len(rate_limited) >= 1, (
            f"Expected at least one 429, got statuses: {responses}"
        )

    async def test_pin_blocked_after_5_failures(self, client, seed_data):
        """PIN bloqueado después de 5 intentos → 429"""
        responses = []
        for i in range(6):
            resp = await client.post("/api/clock", json={
                "pin": "0000",
                "type": "in",
                "tenant_id": seed_data["tenant_a_id"],
            })
            responses.append(resp.status_code)

        # At least one should be 429 (blocked)
        blocked = [s for s in responses if s == 429]
        assert len(blocked) >= 1, (
            f"Expected at least one 429 (blocked), got statuses: {responses}"
        )

    async def test_expired_token(self, client, seed_data):
        """Token expirado → 401"""
        from app.auth import create_access_token
        from datetime import timedelta

        # Create a token that expires immediately
        expired_token = create_access_token(
            {"sub": seed_data["owner_a_id"], "email": "test@test.com", "role": "owner"},
            expires_delta=timedelta(seconds=-1),
        )

        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    async def test_cross_tenant_access_denied(self, client, seed_data):
        """Owner A no puede ver employees de tenant B"""
        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        body = resp.json()
        emp_names = [e["name"] for e in body]
        assert "Pedro TenantB" not in emp_names
        assert "Carlos López" in emp_names


# ═══════════════════════════════════════════════════════════════════════════
# 10. INCIDENTS
# ═══════════════════════════════════════════════════════════════════════════

class TestIncidents:
    """Incident detection: late, no_clock_in, early_leave"""

    async def test_detect_late(self, client, seed_data, db_session):
        """Detectar retraso (fichó después de inicio + tolerancia)"""
        from app.incidents import detect_incidents
        from app.models.schedule import Schedule
        from app.models.clock_in import ClockIn
        from datetime import datetime, time, timezone

        target_date = date.today()

        # Create a schedule for emp1 with morning shift
        sched = Schedule(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp1_id"],
            shift_id=seed_data["shift_morning_id"],
            date=target_date,
        )
        db_session.add(sched)
        await db_session.flush()

        # Create a clock-in that's late (after 08:00 + 5min tolerance = 08:05)
        late_time = datetime.combine(target_date, time(9, 0), tzinfo=timezone.utc)
        clock = ClockIn(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp1_id"],
            type="in",
            timestamp=late_time,
        )
        db_session.add(clock)
        await db_session.commit()

        # Run incident detection
        new_incidents = await detect_incidents(db_session, seed_data["tenant_a_id"], target_date)
        await db_session.commit()

        # Check that a 'late' incident was created
        late_incidents = [i for i in new_incidents if i.type == "late"]
        assert len(late_incidents) >= 1, f"No late incident detected. New incidents: {[i.type for i in new_incidents]}"

    async def test_detect_no_clock_in(self, client, seed_data, db_session):
        """Detectar no_clock_in (empleado con turno sin fichar)"""
        from app.incidents import detect_incidents
        from app.models.schedule import Schedule

        target_date = date.today()

        # Create a schedule for emp2 with no clock-in
        sched = Schedule(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp2_id"],
            shift_id=seed_data["shift_afternoon_id"],
            date=target_date,
        )
        db_session.add(sched)
        await db_session.commit()

        # Run incident detection
        new_incidents = await detect_incidents(db_session, seed_data["tenant_a_id"], target_date)
        await db_session.commit()

        # Check that a 'no_clock_in' incident was created
        no_clock = [i for i in new_incidents if i.type == "no_clock_in"]
        assert len(no_clock) >= 1, f"No no_clock_in incident detected. New incidents: {[i.type for i in new_incidents]}"

    async def test_detect_early_leave(self, client, seed_data, db_session):
        """Detectar salida_anticipada"""
        from app.incidents import detect_incidents
        from app.models.schedule import Schedule
        from app.models.clock_in import ClockIn
        from datetime import datetime, time, timezone

        target_date = date.today()

        # Create a schedule for emp1 with morning shift (08:00-16:00, tolerance 5min)
        sched = Schedule(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp1_id"],
            shift_id=seed_data["shift_morning_id"],
            date=target_date,
        )
        db_session.add(sched)
        await db_session.flush()

        # Create clock-in at 07:55 (on time)
        clock_in = ClockIn(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp1_id"],
            type="in",
            timestamp=datetime.combine(target_date, time(7, 55), tzinfo=timezone.utc),
        )
        db_session.add(clock_in)
        await db_session.flush()

        # Create clock-out at 14:00 (early — shift ends at 16:00, tolerance 5min, so before 15:55)
        clock_out = ClockIn(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp1_id"],
            type="out",
            timestamp=datetime.combine(target_date, time(14, 0), tzinfo=timezone.utc),
        )
        db_session.add(clock_out)
        await db_session.commit()

        # Run incident detection
        new_incidents = await detect_incidents(db_session, seed_data["tenant_a_id"], target_date)
        await db_session.commit()

        # Check that an 'early_leave' incident was created
        early = [i for i in new_incidents if i.type == "early_leave"]
        assert len(early) >= 1, f"No early_leave incident detected. New incidents: {[i.type for i in new_incidents]}"
