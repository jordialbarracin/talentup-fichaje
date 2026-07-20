"""
TalentUP Fichaje — Security tests.
Covers: SQL injection, JWT tampering/expired, XSS, IDOR, cross-tenant,
rate limiting, Stripe webhook auth, public endpoints, WebSocket privacy,
body size limits.
"""
import json
import time as _time
from datetime import datetime, timezone, timedelta

import pytest
from jose import jwt
from jose.utils import base64url_decode, base64url_encode


# ═══════════════════════════════════════════════════════════════════════════
# 1. SQL INJECTION
# ═══════════════════════════════════════════════════════════════════════════

class TestSqlInjection:
    """SQLi attempts must not authenticate or expose foreign data."""

    async def test_login_sql_injection(self, client, seed_data):
        """POST /api/auth/login con email SQLi → 401"""
        resp = await client.post("/api/auth/login", json={
            "email": "admin@x.com' OR 1=1 --",
            "password": "cualquiera",
        })
        assert resp.status_code == 401

    async def test_employees_search_sql_injection(self, client, seed_data):
        """GET /api/employees?search=... con SQLi → 200, sin datos inyectados"""
        resp = await client.get(
            "/api/employees?search=' OR 1=1 --",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        items = body["items"]
        # No debe incluir empleados del tenant B (aislamiento + no inyección)
        names = [e["name"] for e in items]
        assert "Pedro TenantB" not in names
        # Sólo empleados del tenant A
        assert all(e["tenant_id"] == seed_data["tenant_a_id"] for e in items)


# ═══════════════════════════════════════════════════════════════════════════
# 2. JWT TAMPERING / EXPIRED
# ═══════════════════════════════════════════════════════════════════════════

class TestJwtSecurity:
    """JWT integrity and expiration enforcement."""

    async def test_jwt_tampering(self, client, seed_data):
        """Modificar payload del token → 401"""
        token = seed_data["owner_a_token"]
        parts = token.split(".")
        payload = json.loads(
            base64url_decode(parts[1].encode("utf-8") + b"==").decode("utf-8")
        )
        payload["role"] = "super_admin"
        tampered_payload = base64url_encode(
            json.dumps(payload).encode("utf-8")
        ).decode("utf-8").rstrip("=")
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert resp.status_code == 401

    async def test_jwt_expired(self, client, seed_data):
        """Token expirado en el pasado → 401"""
        from app.auth import SECRET_KEY, ALGORITHM
        expired_token = jwt.encode(
            {
                "sub": seed_data["owner_a_id"],
                "email": "owner@latagliatella.es",
                "role": "owner",
                "tenant_id": seed_data["tenant_a_id"],
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 3. CROSS-TENANT ISOLATION
# ═══════════════════════════════════════════════════════════════════════════

class TestCrossTenant:
    """Users must not access data from another tenant."""

    async def test_cross_tenant_employees(self, client, seed_data):
        """Token de tenant A solo devuelve empleados de A"""
        resp = await client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        items = body["items"]
        tenant_ids = {e["tenant_id"] for e in items}
        assert tenant_ids == {seed_data["tenant_a_id"]}

    async def test_cross_tenant_billing_status(self, client, seed_data):
        """Token de tenant A consulta billing/status/{tenant_b_id} → 403"""
        resp = await client.get(
            f"/api/billing/status/{seed_data['tenant_b_id']}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# 4. XSS
# ═══════════════════════════════════════════════════════════════════════════

class TestXss:
    """Stored values with scripts must be escaped/normalized in responses."""

    async def test_create_employee_xss_name(self, client, seed_data):
        """POST /api/employees con name <script> → 201 pero escapado"""
        xss_name = "<script>alert(1)</script>"
        resp = await client.post(
            "/api/employees",
            json={
                "name": xss_name,
                "dni": "55555555X",
                "pin": "0000",
                "is_active": True,
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        returned = body["name"]
        # No debe devolver el script literal como HTML ejecutable
        assert "<script>" not in returned
        assert "</script>" not in returned
        # El contenido sigue siendo reconocible (escapado, no borrado)
        assert "alert(1)" in returned


# ═══════════════════════════════════════════════════════════════════════════
# 5. IDOR
# ═══════════════════════════════════════════════════════════════════════════

class TestIdor:
    """Direct object references across tenants must be rejected."""

    async def test_get_employee_from_other_tenant(self, client, seed_data):
        """GET /api/employees/{emp_b1_id} con token de A → 403 o 404"""
        resp = await client.get(
            f"/api/employees/{seed_data['emp_b1_id']}",
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code in (403, 404)


# ═══════════════════════════════════════════════════════════════════════════
# 6. RATE LIMITING
# ═══════════════════════════════════════════════════════════════════════════

class TestRateLimiting:
    """Clock endpoints rate-limit after 10 req/minute."""

    async def test_rate_limit_nfc(self, client, seed_data):
        """15 POST /api/clock/nfc → 429 tras el 10"""
        tenant_id = seed_data["tenant_a_id"]
        statuses = []
        for i in range(15):
            resp = await client.post("/api/clock/nfc", json={
                "nfc_uid": "NFC001",
                "tenant_id": tenant_id,
            })
            statuses.append(resp.status_code)

        # Las primeras 10 deben ser 201; a partir de la 11 debe llegar 429
        assert statuses[:10].count(201) == 10, statuses
        assert any(s == 429 for s in statuses[10:]), statuses

    async def test_rate_limit_pin_wrong(self, client, seed_data):
        """15 POST /api/clock con PIN incorrecto → 429 tras el 10"""
        tenant_id = seed_data["tenant_a_id"]
        statuses = []
        for i in range(15):
            resp = await client.post("/api/clock", json={
                "pin": "0000",
                "type": "in",
                "tenant_id": tenant_id,
            })
            statuses.append(resp.status_code)

        # Tras varios intentos fallidos debe activarse bloqueo 429
        assert statuses.count(401) >= 4, statuses
        assert any(s == 429 for s in statuses), statuses


# ═══════════════════════════════════════════════════════════════════════════
# 7. STRIPE WEBHOOK
# ═══════════════════════════════════════════════════════════════════════════

class TestStripeWebhook:
    """Stripe webhook endpoints require a valid signature."""

    async def test_stripe_webhook_missing_signature(self, client, seed_data):
        """POST /api/billing/webhook sin Stripe-Signature → 400"""
        resp = await client.post(
            "/api/billing/webhook",
            json={"type": "invoice.paid", "data": {"object": {}}},
        )
        assert resp.status_code == 400

    async def test_stripe_webhook_invalid_signature(self, client, seed_data):
        """POST /api/billing/webhook con firma falsa → 400"""
        resp = await client.post(
            "/api/billing/webhook",
            json={"type": "invoice.paid", "data": {"object": {}}},
            headers={"stripe-signature": "t=1,v1=fakesignature"},
        )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════
# 8. PUBLIC ENDPOINT / AUTH
# ═══════════════════════════════════════════════════════════════════════════

class TestPublicEndpoints:
    """Protected endpoints reject unauthenticated requests."""

    async def test_employees_without_token(self, client, seed_data):
        """GET /api/employees sin token → 401"""
        resp = await client.get("/api/employees")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# 9. WEBSOCKET WITHOUT AUTH
# ═══════════════════════════════════════════════════════════════════════════

class TestWebSocket:
    """Public WebSocket does not leak sensitive data."""

    async def test_ws_nfc_public_no_sensitive_data(self, client, seed_data):
        """Conectar a /ws/nfc: acepta y recibe sólo mensajes públicos"""
        from starlette.testclient import TestClient
        from app.main import app
        with TestClient(app) as test_client:
            with test_client.websocket_connect("/ws/nfc") as ws:
                initial = ws.receive_json()
                assert initial["type"] == "nfc_connected"
                # No debe contener datos sensibles (pin, tenant_id, empleado privado)
                payload = json.dumps(initial)
                assert "pin" not in payload.lower()
                assert "tenant_id" not in payload.lower()
                assert "password" not in payload.lower()
                assert "dni" not in payload.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 10. BODY SIZE LIMIT
# ═══════════════════════════════════════════════════════════════════════════

class TestBodySize:
    """Large request bodies are rejected."""

    async def test_body_size_limit(self, client, seed_data):
        """POST /api/employees con body > 1MB → 413"""
        big_name = "A" * (2 * 1024 * 1024)
        resp = await client.post(
            "/api/employees",
            json={
                "name": big_name,
                "dni": "99999999Y",
                "pin": "0000",
            },
            headers={"Authorization": f"Bearer {seed_data['owner_a_token']}"},
        )
        assert resp.status_code == 413
