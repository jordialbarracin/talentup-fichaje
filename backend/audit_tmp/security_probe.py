"""
TalentUP Fichaje DEFINITIVO v3 — Security audit probes.
Uses httpx.ASGITransport to hit the app directly, bypassing IP-based register rate limits.
Set PIN_HASH_SALT, JWT_SECRET, and dummy Stripe env vars so the app boots in test mode.
"""
import os, sys, json, base64, hmac, hashlib, time

# Make backend importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./audit_test.db")
os.environ.setdefault("PIN_HASH_SALT", "audit-salt-32-bytes-long-value")
os.environ.setdefault("JWT_SECRET", "audit-jwt-secret-32-bytes-long-value")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy_for_audit")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_webhook_secret_32bytes_long")

import httpx
from app.main import app
from app.database import init_db

BASE = "http://test/api"
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"

results = {}

def record(name, ok, detail=""):
    results[name] = (ok, detail)
    tag = PASS if ok else FAIL
    print(f"[{tag}] {name}: {detail}")

async def main():
    await init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE) as c:
        # 1. Health + CSP
        r = await c.get("/health")
        csp = r.headers.get("content-security-policy", "")
        print("CSP:", csp)
        has_nonce = "nonce-" in csp
        no_unsafe_script = "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0] if "script-src" in csp else False
        record("CSP nonce", has_nonce and no_unsafe_script, f"nonce={has_nonce}, script-src no unsafe-inline={no_unsafe_script}")

        # 2. Body limit
        big = {"payload": "a" * (1024 * 1100)}
        r = await c.post("/auth/login", json=big)
        record("Body limit 413", r.status_code == 413, f"status={r.status_code}")

        # 3. XSS register
        uid = str(int(time.time()))
        r = await c.post("/auth/register", json={
            "restaurant_name": f"XSSTest{uid}",
            "owner_name": "<script>alert(1)</script>",
            "email": f"xss{uid}@example.com",
            "password": "xsspass123",
        })
        escaped = False
        if r.status_code == 201:
            data = r.json()
            name = data.get("user", {}).get("name", "")
            rn = data.get("user", {}).get("tenant_name") or data.get("tenant_id")
            escaped = "<script>" not in name
            print("owner_name returned:", repr(name))
            record("XSS register escaped", escaped, f"name={name!r}")
        else:
            record("XSS register escaped", False, f"status={r.status_code} {r.text[:120]}")

        # 4. SQLi login
        r = await c.post("/auth/login", json={"email": "admin@example.com' OR '1'='1", "password": "x"})
        record("SQLi login", r.status_code in (401, 422), f"status={r.status_code}")

        # 5. JWT cookie / tampering / httpOnly
        r = await c.post("/auth/register", json={
            "restaurant_name": f"JWTTest{uid}",
            "owner_name": "JWT",
            "email": f"jwt{uid}@example.com",
            "password": "jwtpass123",
        })
        if r.status_code != 201:
            record("JWT cookie / tampering", False, f"register failed {r.status_code}")
        else:
            data = r.json()
            access = data["access_token"]
            refresh = data["refresh_token"]
            # cookie should be httOnly and secure
            set_cookie = r.headers.get("set-cookie", "")
            print("Set-Cookie header:", set_cookie)
            httponly = "HttpOnly" in set_cookie
            secure = "Secure" in set_cookie
            samesite = "SameSite" in set_cookie
            record("JWT httpOnly cookie", httponly and secure and samesite,
                   f"HttpOnly={httponly}, Secure={secure}, SameSite={samesite}")

            # tampered token
            h_part, p_part, s_part = access.split('.')
            payload = json.loads(base64.urlsafe_b64decode(p_part + '=' * (-len(p_part) % 4)).decode())
            fake_payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            fake_sig = base64.urlsafe_b64encode(
                hmac.new(b'fake', f"{h_part}.{fake_payload_b64}".encode(), hashlib.sha256).digest()
            ).decode().rstrip('=')
            fake = f"{h_part}.{fake_payload_b64}.{fake_sig}"
            r_tamper = await c.get("/auth/me", headers={"Authorization": f"Bearer {fake}"})
            record("JWT tampering rejected", r_tamper.status_code == 401, f"status={r_tamper.status_code}")

            # refresh endpoint accepts valid refresh token
            r_refresh = await c.post("/auth/refresh", json={"refresh_token": refresh})
            record("Refresh token flow", r_refresh.status_code == 200 and "access_token" in r_refresh.json(),
                   f"status={r_refresh.status_code}")

        # 6. PIN hash salt must be present (env)
        from app.auth import _SECRET_SALT
        record("PIN_HASH_SALT configured", bool(_SECRET_SALT) and len(_SECRET_SALT) > 0, f"len={len(_SECRET_SALT)}")

        # 7. Stripe webhook fail-closed
        r = await c.post("/billing/webhook", json={"type": "checkout.session.completed"})
        record("Stripe webhook no signature 403", r.status_code == 403, f"status={r.status_code} body={r.text[:80]}")

        # 8. Rate limiting register (already tested 3/hour)
        # Since ASGI transport has same client IP (None), 3rd register above should have succeeded and a 4th should 429
        r = await c.post("/auth/register", json={
            "restaurant_name": f"RLTest{uid}",
            "owner_name": "RL",
            "email": f"rl{uid}@example.com",
            "password": "rlpass123",
        })
        record("Register rate limit 429", r.status_code == 429, f"status={r.status_code}")

        # 9. PIN clock rate limiting
        # create a tenant and employee, then hit PIN endpoint 15 times
        r = await c.post("/auth/register", json={
            "restaurant_name": f"PINRest{uid}",
            "owner_name": "PIN",
            "email": f"pin{uid}@example.com",
            "password": "pinpass123",
        })
        if r.status_code == 201:
            token = r.json()["access_token"]
            tenant_id = r.json()["tenant_id"]
            r2 = await c.post("/employees", headers={"Authorization": f"Bearer {token}"}, json={
                "name": "PIN Emp", "pin": "9876", "clock_method": "pin"
            })
            print("employee create:", r2.status_code, r2.text[:120])
            codes = []
            for i in range(15):
                rr = await c.post("/clock", json={"tenant_id": tenant_id, "pin": "9876", "type": "in"})
                codes.append(rr.status_code)
                if i == 0:
                    print("first clock:", rr.status_code, rr.text[:80])
            print("PIN clock codes:", codes)
            has_429 = 429 in codes
            record("PIN clock rate limit 429", has_429, f"codes={codes[:12]}...")
        else:
            record("PIN clock rate limit 429", False, f"register failed {r.status_code}")

        # 10. NFC clock rate limiting
        r = await c.post("/auth/register", json={
            "restaurant_name": f"NFCRest{uid}",
            "owner_name": "NFC",
            "email": f"nfc{uid}@example.com",
            "password": "nfcpass123",
        })
        if r.status_code == 201:
            token = r.json()["access_token"]
            tenant_id = r.json()["tenant_id"]
            await c.post("/employees", headers={"Authorization": f"Bearer {token}"}, json={
                "name": "NFC Emp", "pin": "1234", "nfc_uid": "A1B2C3D4", "clock_method": "nfc"
            })
            codes = []
            for i in range(15):
                rr = await c.post("/clock/nfc", json={"tenant_id": tenant_id, "nfc_uid": "A1B2C3D4"})
                codes.append(rr.status_code)
            print("NFC clock codes:", codes)
            record("NFC clock rate limit 429", 429 in codes, f"codes={codes[:12]}...")
        else:
            record("NFC clock rate limit 429", False, f"register failed {r.status_code}")

    print("\n=== SUMMARY ===")
    for name, (ok, detail) in results.items():
        tag = PASS if ok else FAIL
        print(f"[{tag}] {name}: {detail}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
