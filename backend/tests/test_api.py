"""
TalentUP Fichaje — Automated API tests.
Tests auth, clock (fichaje), employees, and reports endpoints.
"""
import pytest
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════
# 1. AUTH
# ═══════════════════════════════════════════════════════════════════════════

class TestAuth:
    """POST /api/auth/login and GET /api/auth/me"""

    async def test_login_correct_credentials(self, client, seed_data):
        """Login with correct credentials → 200 + access_token"""
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

    async def test_login_incorrect_credentials(self, client, seed_data):
        """Login with wrong password → 401"""
        resp = await client.post("/api/auth/login", json={
            "email": "owner@latagliatella.es",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        body = resp.json()
        assert "detail" in body

    async def test_login_nonexistent_user(self, client, seed_data):
        """Login with non-existent email → 401"""
        resp = await client.post("/api/auth/login", json={
            "email": "noone@example.com",
            "password": "anything",
        })
        assert resp.status_code == 401

    async def test_me_with_valid_token(self, client, seed_data):
        """GET /api/auth/me with valid token → 200 + user data"""
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "owner@latagliatella.es"
        assert body["role"] == "owner"
        assert "id" in body

    async def test_me_without_token(self, client, seed_data):
        """GET /api/auth/me without token → 401"""
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401
        body = resp.json()
        assert "detail" in body

    async def test_me_with_invalid_token(self, client, seed_data):
        """GET /api/auth/me with garbage token → 401"""
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer this-is-not-a-valid-jwt"},
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 2. CLOCK (FICHAJE)
# ═══════════════════════════════════════════════════════════════════════════

class TestClock:
    """POST /api/clock (public, PIN-based) and GET /api/clock/*"""

    async def test_clock_in_valid_pin(self, client, seed_data):
        """Clock in with valid PIN + type 'in' → 201"""
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
        """Clock in then out with valid PIN → both 201"""
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
        """Clock with invalid PIN → 401 (code returns 401, not 404)"""
        resp = await client.post("/api/clock", json={
            "pin": "0000",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp.status_code == 401
        body = resp.json()
        assert "PIN incorrecto" in body["detail"]

    async def test_clock_invalid_type(self, client, seed_data):
        """Clock with invalid type → 400 (code returns 400, not 422)"""
        resp = await client.post("/api/clock", json={
            "pin": "1234",
            "type": "invalid_type_xyz",
            "tenant_id": seed_data["tenant_a_id"],
        })
        assert resp.status_code == 400
        body = resp.json()
        assert "Tipo inválido" in body["detail"]

    async def test_clock_missing_tenant_id(self, client, seed_data):
        """Clock without tenant_id → 400"""
        resp = await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
        })
        assert resp.status_code == 400
        assert "tenant_id es requerido" in resp.json()["detail"]

    async def test_clock_today(self, client, seed_data):
        """GET /api/clock/today → list of today's clock-ins"""
        # First create a clock-in
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })

        # Then fetch today's entries
        resp = await client.get(
            "/api/clock/today",
            headers={"Authorization": f"Bearer {seed_data['manager_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        assert body[0]["type"] == "in"

    async def test_clock_today_unauthorized(self, client, seed_data):
        """GET /api/clock/today without token → 401"""
        resp = await client.get("/api/clock/today")
        assert resp.status_code == 401

    async def test_clock_history(self, client, seed_data):
        """GET /api/clock/history with date range → clock-ins in that range"""
        # Create a clock-in
        await client.post("/api/clock", json={
            "pin": "1234",
            "type": "in",
            "tenant_id": seed_data["tenant_a_id"],
        })

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        resp = await client.get(
            f"/api/clock/history?date_from={today}&date_to={today}",
            headers={"Authorization": f"Bearer {seed_data['manager_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert len(body["items"]) >= 1

    async def test_clock_history_unauthorized(self, client, seed_data):
        """GET /api/clock/history without token → 401"""
        resp = await client.get("/api/clock/history")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 3. EMPLOYEES
# ═══════════════════════════════════════════════════════════════════════════

class TestEmployees:
    """CRUD /api/employees with tenant isolation"""

    async def test_list_employees_with_token(self, client, seed_data):
        """GET /api/employees with owner token → list of employees"""
        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 2  # We seeded 2 employees for tenant A
        names = [e["name"] for e in body]
        assert "Carlos López" in names
        assert "Ana Martínez" in names

    async def test_list_employees_without_token(self, client, seed_data):
        """GET /api/employees without token → 401"""
        resp = await client.get("/api/employees")
        assert resp.status_code == 401

    async def test_list_employees_other_tenant_isolation(self, client, seed_data):
        """GET /api/employees with tenant B token → only sees tenant B employees"""
        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {seed_data['owner_b_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        # Tenant B has 1 employee (Pedro TenantB)
        assert len(body) == 1
        assert body[0]["name"] == "Pedro TenantB"

    async def test_create_employee(self, client, seed_data):
        """POST /api/employees with owner token → 201 + employee data"""
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
        # PIN should NOT be in the response
        assert "pin" not in body
        assert "pin_hash" not in body

    async def test_create_employee_without_token(self, client, seed_data):
        """POST /api/employees without token → 401"""
        resp = await client.post("/api/employees", json={
            "name": "No Auth",
            "pin": "1234",
        })
        assert resp.status_code == 401

    async def test_update_employee(self, client, seed_data):
        """PUT /api/employees/{id} → updated employee"""
        resp = await client.put(
            f"/api/employees/{seed_data['emp1_id']}",
            json={"name": "Carlos Actualizado", "dni": "87654321Z"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Carlos Actualizado"
        assert body["dni"] == "87654321Z"

    async def test_update_employee_not_found(self, client, seed_data):
        """PUT /api/employees/{nonexistent_id} → 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.put(
            f"/api/employees/{fake_id}",
            json={"name": "Ghost"},
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 404

    async def test_delete_employee(self, client, seed_data):
        """DELETE /api/employees/{id} → 204"""
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
        body = resp2.json()
        ids = [e["id"] for e in body]
        assert seed_data["emp1_id"] not in ids

    async def test_delete_employee_not_found(self, client, seed_data):
        """DELETE /api/employees/{nonexistent_id} → 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.delete(
            f"/api/employees/{fake_id}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 404

    async def test_tenant_cannot_see_other_tenant_employees(self, client, seed_data):
        """Tenant A owner cannot see Tenant B's employees via GET"""
        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        body = resp.json()
        emp_names = [e["name"] for e in body]
        assert "Pedro TenantB" not in emp_names
        assert "Carlos López" in emp_names


# ═══════════════════════════════════════════════════════════════════════════
# 4. REPORTS
# ═══════════════════════════════════════════════════════════════════════════

class TestReports:
    """GET /api/reports/hours and GET /api/reports/export"""

    async def test_reports_hours(self, client, seed_data):
        """GET /api/reports/hours with date range → hours per employee"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Create a clock-in/out pair first
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
        # Find Carlos López in the report
        carlos = [e for e in body["employees"] if e["employee_name"] == "Carlos López"]
        assert len(carlos) == 1
        assert carlos[0]["total_hours"] > 0

    async def test_reports_hours_unauthorized(self, client, seed_data):
        """GET /api/reports/hours without token → 401"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        resp = await client.get(
            f"/api/reports/hours?date_from={today}&date_to={today}",
        )
        assert resp.status_code == 401

    async def test_reports_export_pdf(self, client, seed_data):
        """GET /api/reports/export?format=pdf → PDF binary response"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Create some clock data
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
        assert len(resp.content) > 100  # PDF should have meaningful content

    async def test_reports_export_excel(self, client, seed_data):
        """GET /api/reports/export?format=excel → Excel binary response"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Create some clock data
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
        assert len(resp.content) > 100  # Excel should have meaningful content

    async def test_reports_export_unauthorized(self, client, seed_data):
        """GET /api/reports/export without token → 401"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        resp = await client.get(
            f"/api/reports/export?format=pdf&date_from={today}&date_to={today}",
        )
        assert resp.status_code == 401
