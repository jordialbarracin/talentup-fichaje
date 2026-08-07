"""
TalentUP Fichaje — Comprehensive E2E API tests.
Covers: auth, employees, clock, shifts, vacations, leave, holidays, reports, security, incidents.
"""
import pytest
from datetime import datetime, timezone, date, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app


# ═══════════════════════════════════════════════════════════════════════════
# 1. AUTH
# ═══════════════════════════════════════════════════════════════════════════

class TestAuth:
    """POST /api/auth/login and GET /api/auth/me"""

    async def test_login_returns_cookies(self, client, seed_data):
        """Login sets httpOnly access_token and refresh_token cookies."""
        resp = await client.post("/api/auth/login", json={
            "email": "owner@latagliatella.es",
            "password": "owner123",
        })
        assert resp.status_code == 200
        cookies = resp.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert cookies["access_token"]
        assert cookies["refresh_token"]

    async def test_employees_with_cookie_no_header(self, client, seed_data):
        """GET /api/employees works using only the access_token cookie."""
        login = await client.post("/api/auth/login", json={
            "email": "owner@latagliatella.es",
            "password": "owner123",
        })
        assert login.status_code == 200
        access_token = login.cookies["access_token"]

        cookie_client = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            cookies={"access_token": access_token},
            follow_redirects=False,
        )
        async with cookie_client as cc:
            resp = await cc.get("/api/employees")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        names = [e["name"] for e in body["items"]]
        assert "Carlos López" in names

    async def test_refresh_with_cookie(self, client, seed_data):
        """POST /api/auth/refresh using refresh_token cookie sets a new access_token cookie."""
        login = await client.post("/api/auth/login", json={
            "email": "owner@latagliatella.es",
            "password": "owner123",
        })
        assert login.status_code == 200
        refresh_token = login.cookies["refresh_token"]

        refresh_client = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            cookies={"refresh_token": refresh_token},
            follow_redirects=False,
        )
        async with refresh_client as rc:
            resp = await rc.post("/api/auth/refresh")
        assert resp.status_code == 200
        assert "access_token" in resp.cookies
        assert resp.cookies["access_token"]

    async def test_login_correct(self, client, seed_data):
        """Login with correct credentials → 200 + user info, no token in body"""
        resp = await client.post("/api/auth/login", json={
            "email": "owner@latagliatella.es",
            "password": "owner123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert "access_token" not in body
        assert "refresh_token" not in body
        assert "token_type" not in body
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
        assert "items" in body
        items = body["items"]
        assert len(items) >= 2
        names = [e["name"] for e in items]
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
        assert body["dni"] == "*****111H"  # PII masked by default
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
        assert body["dni"] == "*****321Z"  # PII masked by default

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
        items = resp2.json()["items"]
        ids = [e["id"] for e in items]
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
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Pedro TenantB"


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

    # ═══════════════════════════════════════════════════════════════════════
    # NFC CLOCK
    # ═══════════════════════════════════════════════════════════════════════

    async def test_nfc_clock_in_valid(self, client, seed_data):
        """POST /api/clock/nfc con NFC UID válido → 201 (auto in)"""
        resp = await client.post("/api/clock/nfc", json={
            "nfc_uid": "NFC001",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["ok"] is True
        assert body["type"] == "in"
        assert body["employee_name"] == "Carlos López"
        assert "Entrada" in body["message"]
        assert body["clock"]["employee_id"] == seed_data["emp1_id"]
        assert body["clock"]["is_offline"] is False

    async def test_nfc_clock_toggle_in_out(self, client, seed_data):
        """POST /api/clock/nfc toggle: in → out"""
        # First tap: in
        resp1 = await client.post("/api/clock/nfc", json={
            "nfc_uid": "NFC002",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp1.status_code == 201
        assert resp1.json()["type"] == "in"

        # Second tap: out (auto toggle)
        resp2 = await client.post("/api/clock/nfc", json={
            "nfc_uid": "NFC002",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp2.status_code == 201
        body = resp2.json()
        assert body["ok"] is True
        assert body["type"] == "out"
        assert body["employee_name"] == "Ana Martínez"
        assert "Salida" in body["message"]

    async def test_nfc_clock_unregistered_card(self, client, seed_data):
        """POST /api/clock/nfc con NFC UID no registrado → 404"""
        resp = await client.post("/api/clock/nfc", json={
            "nfc_uid": "UNKNOWN_NFC",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp.status_code == 404
        assert "Tarjeta NFC no registrada" in resp.json()["detail"]

    async def test_nfc_clock_wrong_tenant(self, client, seed_data):
        """POST /api/clock/nfc con NFC UID válido pero otro tenant → 404"""
        resp = await client.post("/api/clock/nfc", json={
            "nfc_uid": "NFC001",
            "tenant_id": seed_data["tenant_b_id"],
        })
        assert resp.status_code == 404
        assert "Tarjeta NFC no registrada" in resp.json()["detail"]

    async def test_nfc_clock_missing_fields(self, client, seed_data):
        """POST /api/clock/nfc sin nfc_uid → 422"""
        resp = await client.post("/api/clock/nfc", json={
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp.status_code == 422

        resp2 = await client.post("/api/clock/nfc", json={
            "nfc_uid": "NFC001",
        })
        assert resp2.status_code == 422


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
        assert "items" in body
        items = body["items"]
        assert len(items) >= 2
        names = [s["name"] for s in items]
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
        assert "items" in body
        items = body["items"]
        assert len(items) >= 1
        assert items[0]["status"] == "pending"

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
        assert "items" in body
        items = body["items"]
        assert len(items) >= 1
        # The leave model uses 'type' field in to_dict
        assert items[0]["type"] == "medical"

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
        assert "items" in body
        items = body["items"]
        assert len(items) >= 1
        assert items[0]["name"] == "Navidad"

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
        items = resp2.json()["items"]
        ids = [h["id"] for h in items]
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
        assert carlos[0]["total_hours"] >= 0

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
        items = body["items"]
        emp_names = [e["name"] for e in items]
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
        late_incidents = [i for i in new_incidents if i.incident_type == "late"]
        assert len(late_incidents) >= 1, f"No late incident detected. New incidents: {[i.incident_type for i in new_incidents]}"

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
        no_clock = [i for i in new_incidents if i.incident_type == "no_clock_in"]
        assert len(no_clock) >= 1, f"No no_clock_in incident detected. New incidents: {[i.incident_type for i in new_incidents]}"

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
        early = [i for i in new_incidents if i.incident_type == "early_leave"]
        assert len(early) >= 1, f"No early_leave incident detected. New incidents: {[i.incident_type for i in new_incidents]}"



# ═══════════════════════════════════════════════════════════════════════════
# 11. TENANTS (super_admin only)
# ═══════════════════════════════════════════════════════════════════════════

class TestTenants:
    """CRUD /api/tenants — super_admin only"""

    async def test_list_tenants_as_admin(self, client, seed_data):
        """GET /api/tenants as super_admin → 200 with all tenants"""
        resp = await client.get(
            "/api/tenants",
            headers={"Authorization": f"Bearer {seed_data['admin_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "items" in body
        assert body["total"] >= 2
        names = [t["name"] for t in body["items"]]
        assert "Restaurante La Tagliatella" in names
        assert "Bar El Puerto" in names

    async def test_list_tenants_owner_forbidden(self, client, seed_data):
        """GET /api/tenants as owner → 403"""
        resp = await client.get(
            "/api/tenants",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 403

    async def test_list_tenants_no_token(self, client, seed_data):
        """GET /api/tenants without token → 401"""
        resp = await client.get("/api/tenants")
        assert resp.status_code == 401

    async def test_create_tenant_as_admin(self, client, seed_data):
        """POST /api/tenants as super_admin → 201"""
        resp = await client.post(
            "/api/tenants",
            json={
                "name": "New Restaurant",
                "legal_name": "New Restaurant SL",
                "cif": "B99999999",
                "plan": "premium",
                "tolerancia_min": 10,
            },
            headers={"Authorization": f"Bearer {seed_data['admin_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "New Restaurant"
        assert body["cif"] == "B99999999"
        assert body["plan"] == "premium"
        assert body["tolerancia_min"] == 10
        assert "id" in body

    async def test_create_tenant_owner_forbidden(self, client, seed_data):
        """POST /api/tenants as owner → 403"""
        resp = await client.post(
            "/api/tenants",
            json={"name": "Forbidden Tenant"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 403

    async def test_create_tenant_validation_error(self, client, seed_data):
        """POST /api/tenants with missing required name → 422"""
        resp = await client.post(
            "/api/tenants",
            json={"cif": "B11111111"},
            headers={"Authorization": f"Bearer {seed_data['admin_token']}"},
        )
        assert resp.status_code == 422

    async def test_update_tenant_as_admin(self, client, seed_data):
        """PUT /api/tenants/{id} as super_admin → 200"""
        resp = await client.put(
            f"/api/tenants/{seed_data['tenant_a_id']}",
            json={"name": "Updated Tagliatella", "plan": "enterprise"},
            headers={"Authorization": f"Bearer {seed_data['admin_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Updated Tagliatella"
        assert body["plan"] == "enterprise"

    async def test_update_tenant_not_found(self, client, seed_data):
        """PUT /api/tenants/{nonexistent} → 404"""
        resp = await client.put(
            "/api/tenants/nonexistent-tenant-id",
            json={"name": "Nope"},
            headers={"Authorization": f"Bearer {seed_data['admin_token']}"},
        )
        assert resp.status_code == 404

    async def test_delete_tenant_as_admin(self, client, seed_data):
        """DELETE /api/tenants/{id} as super_admin → 204"""
        # Create a tenant to delete
        resp_create = await client.post(
            "/api/tenants",
            json={"name": "To Delete"},
            headers={"Authorization": f"Bearer {seed_data['admin_token']}"},
        )
        tenant_id = resp_create.json()["id"]

        resp = await client.delete(
            f"/api/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {seed_data['admin_token']}"},
        )
        assert resp.status_code == 204

    async def test_get_tenant_as_admin(self, client, seed_data):
        """GET /api/tenants/{id} as super_admin → 200"""
        resp = await client.get(
            f"/api/tenants/{seed_data['tenant_a_id']}",
            headers={"Authorization": f"Bearer {seed_data['admin_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == seed_data["tenant_a_id"]
        assert body["name"] == "Restaurante La Tagliatella"


# ═══════════════════════════════════════════════════════════════════════════
# 12. CONTRACTS (owner role)
# ═══════════════════════════════════════════════════════════════════════════

class TestContracts:
    """CRUD /api/contracts — owner role"""

    async def test_list_contracts_empty(self, client, seed_data):
        """GET /api/contracts → 200 (empty list initially)"""
        resp = await client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "items" in body
        assert body["total"] == 0
        assert len(body["items"]) == 0

    async def test_list_contracts_no_token(self, client, seed_data):
        """GET /api/contracts without token → 401"""
        resp = await client.get("/api/contracts")
        assert resp.status_code == 401

    async def test_create_contract(self, client, seed_data):
        """POST /api/contracts → 201"""
        resp = await client.post(
            "/api/contracts",
            json={
                "employee_id": seed_data["emp1_id"],
                "contract_type": "indefinido",
                "start_date": "2025-01-01",
                "is_indefinite": True,
                "weekly_hours": 40,
                "salary_base": 1500.00,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["employee_id"] == seed_data["emp1_id"]
        assert body["contract_type"] == "indefinido"
        assert body["start_date"] == "2025-01-01"
        assert body["is_indefinite"] is True
        assert body["tenant_id"] == seed_data["tenant_a_id"]
        assert "id" in body

    async def test_create_contract_validation_error(self, client, seed_data):
        """POST /api/contracts with missing required fields → 422"""
        resp = await client.post(
            "/api/contracts",
            json={"category": "cook"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 422

    async def test_list_contracts_with_filter(self, client, seed_data):
        """GET /api/contracts?employee_id= → filtered list"""
        # Create two contracts for different employees
        await client.post(
            "/api/contracts",
            json={
                "employee_id": seed_data["emp1_id"],
                "contract_type": "indefinido",
                "start_date": "2025-01-01",
                "is_indefinite": True,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        await client.post(
            "/api/contracts",
            json={
                "employee_id": seed_data["emp2_id"],
                "contract_type": "temporal",
                "start_date": "2025-02-01",
                "end_date": "2025-06-30",
                "duration_days": 180,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        # Filter by emp1
        resp = await client.get(
            f"/api/contracts?employee_id={seed_data['emp1_id']}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["employee_id"] == seed_data["emp1_id"]

    async def test_update_contract(self, client, seed_data):
        """PUT /api/contracts/{id} → 200"""
        # Create a contract first
        resp_create = await client.post(
            "/api/contracts",
            json={
                "employee_id": seed_data["emp1_id"],
                "contract_type": "temporal",
                "start_date": "2025-01-01",
                "end_date": "2025-06-30",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        contract_id = resp_create.json()["id"]

        resp = await client.put(
            f"/api/contracts/{contract_id}",
            json={"contract_type": "indefinido", "is_indefinite": True, "status": "active"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["contract_type"] == "indefinido"
        assert body["is_indefinite"] is True

    async def test_delete_contract(self, client, seed_data):
        """DELETE /api/contracts/{id} → 204"""
        resp_create = await client.post(
            "/api/contracts",
            json={
                "employee_id": seed_data["emp1_id"],
                "contract_type": "temporal",
                "start_date": "2025-01-01",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        contract_id = resp_create.json()["id"]

        resp = await client.delete(
            f"/api/contracts/{contract_id}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 204

    async def test_get_contract_not_found(self, client, seed_data):
        """GET /api/contracts/{nonexistent} → 404"""
        resp = await client.get(
            "/api/contracts/nonexistent-contract-id",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 404

    async def test_cross_tenant_contract_isolation(self, client, seed_data):
        """Owner B cannot see contracts from tenant A"""
        # Owner A creates a contract
        await client.post(
            "/api/contracts",
            json={
                "employee_id": seed_data["emp1_id"],
                "contract_type": "indefinido",
                "start_date": "2025-01-01",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        # Owner B sees empty list
        resp = await client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {seed_data['owner_b_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# 13. SCHEDULES (owner role, date filtering)
# ═══════════════════════════════════════════════════════════════════════════

class TestSchedules:
    """CRUD /api/schedules — owner role, date filtering"""

    async def test_list_schedules_empty(self, client, seed_data):
        """GET /api/schedules → 200 (empty initially)"""
        resp = await client.get(
            "/api/schedules",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "items" in body
        assert body["total"] == 0

    async def test_list_schedules_no_token(self, client, seed_data):
        """GET /api/schedules without token → 401"""
        resp = await client.get("/api/schedules")
        assert resp.status_code == 401

    async def test_create_schedule(self, client, seed_data):
        """POST /api/schedules → 201"""
        resp = await client.post(
            "/api/schedules",
            json={
                "employee_id": seed_data["emp1_id"],
                "shift_id": seed_data["shift_morning_id"],
                "date": "2025-06-15",
                "notes": "Morning shift assignment",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["employee_id"] == seed_data["emp1_id"]
        assert body["shift_id"] == seed_data["shift_morning_id"]
        assert body["date"] == "2025-06-15"
        assert body["notes"] == "Morning shift assignment"
        assert body["tenant_id"] == seed_data["tenant_a_id"]

    async def test_create_schedule_duplicate(self, client, seed_data):
        """POST /api/schedules duplicate employee+date → 409"""
        payload = {
            "employee_id": seed_data["emp1_id"],
            "shift_id": seed_data["shift_morning_id"],
            "date": "2025-06-16",
        }
        resp1 = await client.post(
            "/api/schedules",
            json=payload,
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            "/api/schedules",
            json=payload,
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp2.status_code == 409
        assert "Ya existe" in resp2.json()["detail"]

    async def test_create_schedule_invalid_date(self, client, seed_data):
        """POST /api/schedules with invalid date format → 400"""
        resp = await client.post(
            "/api/schedules",
            json={
                "employee_id": seed_data["emp1_id"],
                "shift_id": seed_data["shift_morning_id"],
                "date": "not-a-date",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 400
        assert "Formato de fecha inválido" in resp.json()["detail"]

    async def test_list_schedules_date_filter(self, client, seed_data):
        """GET /api/schedules?date_from=&date_to= → filtered by date range"""
        # Create schedules on different dates
        for d in ["2025-06-10", "2025-06-15", "2025-06-20", "2025-06-25"]:
            await client.post(
                "/api/schedules",
                json={
                    "employee_id": seed_data["emp1_id"],
                    "shift_id": seed_data["shift_morning_id"],
                    "date": d,
                },
                headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
            )

        # Filter date_from=2025-06-12&date_to=2025-06-22
        resp = await client.get(
            "/api/schedules?date_from=2025-06-12&date_to=2025-06-22",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        dates = [s["date"] for s in body["items"]]
        assert "2025-06-15" in dates
        assert "2025-06-20" in dates
        assert "2025-06-10" not in dates
        assert "2025-06-25" not in dates

    async def test_list_schedules_invalid_date_filter(self, client, seed_data):
        """GET /api/schedules?date_from=invalid → 400"""
        resp = await client.get(
            "/api/schedules?date_from=bad-format",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 400
        assert "Formato de fecha inválido" in resp.json()["detail"]

    async def test_update_schedule(self, client, seed_data):
        """PUT /api/schedules/{id} → 200"""
        resp_create = await client.post(
            "/api/schedules",
            json={
                "employee_id": seed_data["emp1_id"],
                "shift_id": seed_data["shift_morning_id"],
                "date": "2025-07-01",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        sched_id = resp_create.json()["id"]

        resp = await client.put(
            f"/api/schedules/{sched_id}",
            json={"shift_id": seed_data["shift_afternoon_id"], "notes": "Changed to afternoon"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["shift_id"] == seed_data["shift_afternoon_id"]
        assert body["notes"] == "Changed to afternoon"

    async def test_delete_schedule(self, client, seed_data):
        """DELETE /api/schedules/{id} → 204"""
        resp_create = await client.post(
            "/api/schedules",
            json={
                "employee_id": seed_data["emp1_id"],
                "shift_id": seed_data["shift_morning_id"],
                "date": "2025-07-02",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        sched_id = resp_create.json()["id"]

        resp = await client.delete(
            f"/api/schedules/{sched_id}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 204

    async def test_get_schedule_not_found(self, client, seed_data):
        """GET /api/schedules/{nonexistent} → 404"""
        resp = await client.get(
            "/api/schedules/nonexistent-schedule-id",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 404

    async def test_cross_tenant_schedule_isolation(self, client, seed_data):
        """Owner B cannot see schedules from tenant A"""
        await client.post(
            "/api/schedules",
            json={
                "employee_id": seed_data["emp1_id"],
                "shift_id": seed_data["shift_morning_id"],
                "date": "2025-08-01",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        resp = await client.get(
            "/api/schedules",
            headers={"Authorization": f"Bearer {seed_data['owner_b_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# 14. OVERTIME (owner role)
# ═══════════════════════════════════════════════════════════════════════════

class TestOvertime:
    """GET/POST /api/overtime, POST /api/overtime/calculate — owner role"""

    async def test_list_overtime_empty(self, client, seed_data):
        """GET /api/overtime → 200 (empty initially)"""
        resp = await client.get(
            "/api/overtime",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "items" in body
        assert body["total"] == 0

    async def test_list_overtime_no_token(self, client, seed_data):
        """GET /api/overtime without token → 401"""
        resp = await client.get("/api/overtime")
        assert resp.status_code == 401

    async def test_create_overtime(self, client, seed_data):
        """POST /api/overtime → 201"""
        resp = await client.post(
            "/api/overtime",
            json={
                "employee_id": seed_data["emp1_id"],
                "date": "2025-06-15",
                "shift_id": seed_data["shift_morning_id"],
                "overtime_type": "structural",
                "total_minutes": 60,
                "compensated_minutes": 0,
                "paid_minutes": 60,
                "hourly_rate_multiplier": 1.75,
                "hourly_rate": 12.50,
                "overtime_amount": 21.88,
                "notes": "Extra hour",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["employee_id"] == seed_data["emp1_id"]
        assert body["total_minutes"] == 60
        assert body["overtime_type"] == "structural"
        assert body["source"] == "manual"
        assert body["tenant_id"] == seed_data["tenant_a_id"]

    async def test_create_overtime_validation_error(self, client, seed_data):
        """POST /api/overtime with missing required fields → 422"""
        resp = await client.post(
            "/api/overtime",
            json={"employee_id": seed_data["emp1_id"]},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 422

    async def test_list_overtime_with_filter(self, client, seed_data):
        """GET /api/overtime?employee_id= → filtered list"""
        await client.post(
            "/api/overtime",
            json={
                "employee_id": seed_data["emp1_id"],
                "date": "2025-06-15",
                "total_minutes": 60,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        await client.post(
            "/api/overtime",
            json={
                "employee_id": seed_data["emp2_id"],
                "date": "2025-06-16",
                "total_minutes": 30,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        resp = await client.get(
            f"/api/overtime?employee_id={seed_data['emp1_id']}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["employee_id"] == seed_data["emp1_id"]
        assert body["items"][0]["employee_name"] == "Carlos López"

    async def test_calculate_overtime_missing_dates(self, client, seed_data):
        """POST /api/overtime/calculate without date_from/date_to → 400"""
        resp = await client.post(
            "/api/overtime/calculate",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 400
        assert "date_from y date_to son requeridos" in resp.json()["detail"]

    async def test_calculate_overtime_no_data(self, client, seed_data):
        """POST /api/overtime/calculate with dates but no clock-ins → 0 created"""
        resp = await client.post(
            "/api/overtime/calculate?date_from=2025-06-01&date_to=2025-06-30",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["created"] == 0
        assert isinstance(body["details"], list)

    async def test_calculate_overtime_with_data(
        self, client, seed_data, db_session
    ):
        """POST /api/overtime/calculate detects overtime from clock-ins"""
        from app.models.schedule import Schedule
        from app.models.clock_in import ClockIn
        from app.models.shift import Shift
        from datetime import datetime, time, timezone, date

        target_date = date(2025, 6, 15)  # Sunday — doesn't matter for overtime calc

        # Create a shift with overtime threshold = 0 so any extra minute counts
        ot_shift = Shift(
            tenant_id=seed_data["tenant_a_id"],
            name="OT Test Shift",
            start_time=time(8, 0),
            end_time=time(12, 0),  # 4h shift
            break_min=0,
            overtime_threshold_min=0,
        )
        db_session.add(ot_shift)
        await db_session.flush()

        # Schedule emp1 to this shift on target_date
        sched = Schedule(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp1_id"],
            shift_id=ot_shift.id,
            date=target_date,
        )
        db_session.add(sched)
        await db_session.flush()

        # Clock in at 08:00, out at 13:30 → 5.5h worked, shift is 4h → 1.5h overtime
        ci_in = ClockIn(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp1_id"],
            type="in",
            timestamp=datetime.combine(target_date, time(8, 0), tzinfo=timezone.utc),
        )
        ci_out = ClockIn(
            tenant_id=seed_data["tenant_a_id"],
            employee_id=seed_data["emp1_id"],
            type="out",
            timestamp=datetime.combine(target_date, time(13, 30), tzinfo=timezone.utc),
        )
        db_session.add(ci_in)
        db_session.add(ci_out)
        await db_session.commit()

        resp = await client.post(
            f"/api/overtime/calculate?date_from=2025-06-15&date_to=2025-06-15&employee_id={seed_data['emp1_id']}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["created"] >= 1
        assert len(body["details"]) >= 1
        detail = body["details"][0]
        assert detail["employee_id"] == seed_data["emp1_id"]
        assert detail["minutes"] > 0

    async def test_get_overtime_not_found(self, client, seed_data):
        """GET /api/overtime/{nonexistent} → 404"""
        resp = await client.get(
            "/api/overtime/nonexistent-overtime-id",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 404

    async def test_cross_tenant_overtime_isolation(self, client, seed_data):
        """Owner B cannot see overtime from tenant A"""
        await client.post(
            "/api/overtime",
            json={
                "employee_id": seed_data["emp1_id"],
                "date": "2025-06-15",
                "total_minutes": 60,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        resp = await client.get(
            "/api/overtime",
            headers={"Authorization": f"Bearer {seed_data['owner_b_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# 15. PAYROLL (owner role)
# ═══════════════════════════════════════════════════════════════════════════

class TestPayroll:
    """GET /api/payroll, GET /api/payroll/{month}/{year}, POST /api/payroll/close"""

    async def test_list_payroll_empty(self, client, seed_data):
        """GET /api/payroll → 200 (empty initially)"""
        resp = await client.get(
            "/api/payroll",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "items" in body
        assert body["total"] == 0

    async def test_list_payroll_no_token(self, client, seed_data):
        """GET /api/payroll without token → 401"""
        resp = await client.get("/api/payroll")
        assert resp.status_code == 401

    async def test_get_payroll_by_month_empty(self, client, seed_data):
        """GET /api/payroll/{month}/{year} → 200 empty list when no payrolls"""
        resp = await client.get(
            "/api/payroll/6/2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 0

    async def test_close_payroll_accepted(self, client, seed_data):
        """POST /api/payroll/close?month=6&year=2025 → 202 accepted (background task)"""
        resp = await client.post(
            "/api/payroll/close?month=6&year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["month"] == 6
        assert body["year"] == 2025

    async def test_close_payroll_no_token(self, client, seed_data):
        """POST /api/payroll/close without token → 401"""
        resp = await client.post("/api/payroll/close?month=6&year=2025")
        assert resp.status_code == 401

    async def test_close_payroll_creates_records(self, client, seed_data):
        """POST /api/payroll/close runs background task → payrolls appear in DB"""
        # Close payroll (background task runs synchronously with ASGITransport)
        await client.post(
            "/api/payroll/close?month=9&year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        # Verify payrolls were created by querying the month endpoint
        resp = await client.get(
            "/api/payroll/9/2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        assert body[0]["year"] == 2025
        assert body[0]["month"] == 9
        assert "employee_name" in body[0]
        assert body[0]["status"] == "calculated"

    async def test_get_payroll_by_month_with_filter(self, client, seed_data):
        """GET /api/payroll/{month}/{year}?employee_id= → single record or 404"""
        # Close payroll first
        await client.post(
            "/api/payroll/close?month=10&year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        resp = await client.get(
            f"/api/payroll/10/2025?employee_id={seed_data['emp1_id']}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["employee_id"] == seed_data["emp1_id"]

    async def test_list_payroll_with_year_filter(self, client, seed_data):
        """GET /api/payroll?year=2025 → filtered by year"""
        await client.post(
            "/api/payroll/close?month=11&year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        resp = await client.get(
            "/api/payroll?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert all(p["year"] == 2025 for p in body["items"])

    async def test_cross_tenant_payroll_isolation(self, client, seed_data):
        """Owner B closes payroll and Owner A cannot see it"""
        await client.post(
            "/api/payroll/close?month=6&year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_b_token']}"},
        )

        resp = await client.get(
            "/api/payroll?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        # Owner A should see 0 payrolls (none closed for tenant A yet)
        assert resp.json()["total"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# 16. NOTIFICATIONS (owner role)
# ═══════════════════════════════════════════════════════════════════════════

class TestNotifications:
    """GET/POST /api/notifications, GET /unread, POST /{id}/read"""

    async def test_list_notifications_empty(self, client, seed_data):
        """GET /api/notifications → 200 (empty initially)"""
        resp = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "items" in body
        assert body["total"] == 0

    async def test_list_notifications_no_token(self, client, seed_data):
        """GET /api/notifications without token → 401"""
        resp = await client.get("/api/notifications")
        assert resp.status_code == 401

    async def test_create_notification(self, client, seed_data):
        """POST /api/notifications → 201"""
        resp = await client.post(
            "/api/notifications",
            json={
                "recipient_type": "employee",
                "employee_id": seed_data["emp1_id"],
                "type": "clocking_reminder",
                "title": "Recordatorio fichaje",
                "message": "No olvides fichar al entrar",
                "priority": "normal",
                "category": "clocking",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Recordatorio fichaje"
        assert body["message"] == "No olvides fichar al entrar"
        assert body["type"] == "clocking_reminder"
        assert body["is_read"] is False
        assert body["tenant_id"] == seed_data["tenant_a_id"]
        assert body["sent_at"] is not None

    async def test_create_notification_validation_error(self, client, seed_data):
        """POST /api/notifications with missing required fields → 422"""
        resp = await client.post(
            "/api/notifications",
            json={"type": "test"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 422

    async def test_get_unread_count(self, client, seed_data):
        """GET /api/notifications/unread → count of unread"""
        # Create 3 notifications
        for i in range(3):
            await client.post(
                "/api/notifications",
                json={
                    "type": "info",
                    "title": f"Notice {i}",
                    "message": f"Message {i}",
                },
                headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
            )

        resp = await client.get(
            "/api/notifications/unread",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["unread_count"] == 3

    async def test_get_unread_count_no_token(self, client, seed_data):
        """GET /api/notifications/unread without token → 401"""
        resp = await client.get("/api/notifications/unread")
        assert resp.status_code == 401

    async def test_mark_notification_read(self, client, seed_data):
        """POST /api/notifications/{id}/read → 200 with is_read=True"""
        # Create a notification
        resp_create = await client.post(
            "/api/notifications",
            json={
                "type": "info",
                "title": "Test Notice",
                "message": "Read me",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        notif_id = resp_create.json()["id"]

        # Mark as read
        resp = await client.post(
            f"/api/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_read"] is True
        assert body["read_at"] is not None

    async def test_mark_read_not_found(self, client, seed_data):
        """POST /api/notifications/{nonexistent}/read → 404"""
        resp = await client.post(
            "/api/notifications/nonexistent-id/read",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 404

    async def test_list_notifications_unread_only(self, client, seed_data):
        """GET /api/notifications?unread_only=true → only unread"""
        # Create 2 notifications
        resp1 = await client.post(
            "/api/notifications",
            json={"type": "info", "title": "N1", "message": "M1"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        await client.post(
            "/api/notifications",
            json={"type": "info", "title": "N2", "message": "M2"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        # Mark first as read
        await client.post(
            f"/api/notifications/{resp1.json()['id']}/read",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        # Query unread_only
        resp = await client.get(
            "/api/notifications?unread_only=true",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "N2"

    async def test_cross_tenant_notification_isolation(self, client, seed_data):
        """Owner B cannot see notifications from tenant A"""
        await client.post(
            "/api/notifications",
            json={"type": "info", "title": "Tenant A Notice", "message": "Secret"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        resp = await client.get(
            "/api/notifications",
            headers={"Authorization": f"Bearer {seed_data['owner_b_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# 17. CALENDAR (owner role)
# ═══════════════════════════════════════════════════════════════════════════

class TestCalendar:
    """GET /api/calendar?year=, POST /api/calendar/generate?year="""

    async def test_get_calendar_empty(self, client, seed_data):
        """GET /api/calendar?year=2025 → 200 (empty before generate)"""
        resp = await client.get(
            "/api/calendar?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "items" in body
        assert body["total"] == 0

    async def test_get_calendar_no_token(self, client, seed_data):
        """GET /api/calendar without token → 401"""
        resp = await client.get("/api/calendar?year=2025")
        assert resp.status_code == 401

    async def test_generate_calendar(self, client, seed_data):
        """POST /api/calendar/generate?year=2025 → 200 with 365/366 days"""
        resp = await client.post(
            "/api/calendar/generate?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["year"] == 2025
        assert body["days_generated"] == 365  # 2025 is not a leap year

    async def test_generate_calendar_no_token(self, client, seed_data):
        """POST /api/calendar/generate without token → 401"""
        resp = await client.post("/api/calendar/generate?year=2025")
        assert resp.status_code == 401

    async def test_generate_calendar_duplicate(self, client, seed_data):
        """POST /api/calendar/generate twice → 400 on second call"""
        resp1 = await client.post(
            "/api/calendar/generate?year=2026",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp1.status_code == 200

        resp2 = await client.post(
            "/api/calendar/generate?year=2026",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp2.status_code == 400
        assert "ya existe" in resp2.json()["detail"]

    async def test_get_calendar_after_generate(self, client, seed_data):
        """GET /api/calendar?year= after generate → 365 days via items"""
        await client.post(
            "/api/calendar/generate?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        resp = await client.get(
            "/api/calendar?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 365
        assert len(body["items"]) == 365
        # Check first entry structure
        first = body["items"][0]
        assert first["date"] == "2025-01-01"
        assert first["year"] == 2025
        assert "day_type" in first
        assert "is_working_day" in first
        assert "is_holiday" in first
        assert "is_weekend" in first

    async def test_get_calendar_has_weekends(self, client, seed_data):
        """GET /api/calendar?year= → weekends marked correctly"""
        await client.post(
            "/api/calendar/generate?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )

        resp = await client.get(
            "/api/calendar?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        body = resp.json()
        weekends = [d for d in body["items"] if d["is_weekend"]]
        assert len(weekends) == 104  # 52 Saturdays + 52 Sundays in 2025

    async def test_generate_calendar_leap_year(self, client, seed_data):
        """POST /api/calendar/generate?year=2024 → 366 days (leap year)"""
        resp = await client.post(
            "/api/calendar/generate?year=2024",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["days_generated"] == 366

    async def test_cross_tenant_calendar_isolation(self, client, seed_data):
        """Owner B generates calendar but Owner A sees nothing"""
        await client.post(
            "/api/calendar/generate?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_b_token']}"},
        )

        resp = await client.get(
            "/api/calendar?year=2025",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

# ═══════════════════════════════════════════════════════════════════════════
# EXPORT ASYNC — job_id validation
# ═══════════════════════════════════════════════════════════════════════════

class TestExportAsync:
    """GET /api/reports/export/status and /download — job_id validation"""

    async def test_export_status_invalid_job_id(self, client, seed_data):
        """Invalid job_id (glob chars) → 422"""
        login = await client.post("/api/auth/login", json={
            "email": "owner@latagliatella.es",
            "password": "owner123",
        })
        assert login.status_code == 200
        token = login.cookies["access_token"]

        cookie_client = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            cookies={"access_token": token},
        )
        async with cookie_client as cc:
            # Glob injection attempt
            resp = await cc.get("/api/reports/export/status/*")
            assert resp.status_code == 422

            # Path traversal attempt (URL-decoded by FastAPI)
            resp = await cc.get("/api/reports/export/status/not-a-valid-uuid")
            assert resp.status_code == 422

            # Valid UUID but not found
            resp = await cc.get("/api/reports/export/status/550e8400-e29b-41d4-a716-446655440000")
            assert resp.status_code == 200
            assert resp.json()["status"] == "pending"
