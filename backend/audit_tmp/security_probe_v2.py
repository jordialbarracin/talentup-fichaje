"""
TalentUP Fichaje DEFINITIVO v3 — Security audit probes v2.
Uses httpx.ASGITransport to hit the app directly with a fresh SQLite DB.
Set PIN_HASH_SALT, JWT_SECRET, and dummy Stripe env vars.
"""
import os, sys, json, base64, hmac, hashlib, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./audit_test_v2.db"
os.environ["PIN_HASH_SALT"] = "audit-salt-32-bytes-long-value"
os.environ["JWT_SECRET"] = "audit-jwt-secret-32-bytes-long-value"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy_for_audit"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_webhook_secret_32bytes_long"

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

def parse_cookies(set_cookie: str):
    cookies = {}
    for part in set_cookie.split(","):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k] = v.split(";")[0]
    return cookies

async def main():
    if os.path.exists("audit_test_v2.db"):
        os.remove("audit_test_v2.db")
    await init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE) as c:
        uid_base = str(int(time.time()))

        # 1. CSP nonce
        r = await c.get("/health")
        csp = r.headers.get("content-security-policy", "")
        has_nonce = "nonce-" in csp
        no_unsafe_script = True
        if "script-src" in csp:
            script_part = csp.split("script-src")[1].split(";")[0]
            no_unsafe_script = "'unsafe-inline'" not in script_part
        record("CSP nonce", has_nonce and no_unsafe_script, f"nonce={has_nonce}, no unsafe-inline={no_unsafe_script}")

        # 2. Body limit
        big = {"payload": "a" * (1024 * 1100)}
        r = await c.post("/auth/login", json=big)
        record("Body limit 413", r.status_code == 413, f"status={r.status_code}")

        # 3. XSS register
        r = await c.post("/auth/register", json={
            "restaurant_name": f"XSSTest{uid_base}",
            "owner_name": "<script>alert(1)</script>",
            "email": f"xss{uid_base}@example.com",
            "password": "xsspass123",
        })
        if r.status_code == 201:
            data = r.json()
            name = data.get("user", {}).get("name", "")
            escaped = "<script>" not in name and "<script>" not in name
            record("XSS register escaped", escaped, f"name={name!r}")
        else:
            record("XSS register escaped", False, f"status={r.status_code} {r.text[:120]}")

        # 4. SQLi login
        r = await c.post("/auth/login", json={"email": "admin@example.com' OR '1'='1", "password": "x"})
        record("SQLi login", r.status_code in (401, 422), f"status={r.status_code}")

        # 5. JWT cookie / tampering / refresh
        r = await c.post("/auth/register", json={
            "restaurant_name": f"JWTTest{uid_base}",
            "owner_name": "JWT",
            "email": f"jwt{uid_base}@example.com",
            "password": "jwtpass123",
        })
        if r.status_code != 201:
            record("JWT httpOnly cookie", False, f"register failed {r.status_code}")
            record("JWT tampering rejected", False, "register failed")
            record("Refresh token flow", False, "register failed")
        else:
            data = r.json()
            access = data["access_token"]
            refresh = data["refresh_token"]
            cookies = parse_cookies(r.headers.get("set-cookie", ""))
            print("Cookies parsed:", {k: v[:20]+"..." for k,v in cookies.items()})
            set_cookie = r.headers.get("set-cookie", "")
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

            # refresh with cookie + body fallback
            cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
            r_refresh = await c.post("/auth/refresh", json={"refresh_token": refresh},
                                     headers={"Cookie": cookie_header})
            print("Refresh response:", r_refresh.status_code, r_refresh.text[:200])
            record("Refresh token flow", r_refresh.status_code == 200 and "access_token" in r_refresh.json(),
                   f"status={r_refresh.status_code}")

        # 6. PIN hash salt
        from app.auth import _SECRET_SALT
        record("PIN_HASH_SALT configured", bool(_SECRET_SALT) and len(_SECRET_SALT) > 0, f"len={len(_SECRET_SALT)}")

        # 7. Stripe webhook fail-closed
        r = await c.post("/billing/webhook", json={"type": "checkout.session.completed"})
        print("Stripe no-sig:", r.status_code, r.text[:80])
        # Send an invalid signature
        r2 = await c.post("/billing/webhook", json={"type": "checkout.session.completed"},
                          headers={"stripe-signature": "fake_signature"})
        print("Stripe fake-sig:", r2.status_code, r2.text[:80])
        record("Stripe webhook fail-closed", r.status_code in (400, 403) and r2.status_code in (400, 403),
               f"no-sig={r.status_code}, fake-sig={r2.status_code}")

        # 8. Register rate limit (4 attempts should 429 on 4th)
        codes = []
        for i in range(4):
            rr = await c.post("/auth/register", json={
                "restaurant_name": f"RLTest{uid_base}_{i}",
                "owner_name": "RL",
                "email": f"rl{uid_base}_{i}@example.com",
                "password": "rlpass123",
            })
            codes.append(rr.status_code)
        print("Register codes:", codes)
        record("Register rate limit 429", 429 in codes, f"codes={codes}")

        # 9. PIN clock rate limiting
        # Create tenant+employee for PIN; must be before register rate limit? No, create just after maybe
        # Use a fresh client with different IP? Not possible. Instead use same client but register limit already hit.
        # We'll create tenant/employee NOW (before register limit exhaustion) using remaining allowance.
        # Actually we already used: XSS(1), JWT(1), plus 4 rate-limit registers = 6. We are blocked.
        # We need to reset attempts. Since no Redis, in-memory store resets with new process.
        # Re-create client after init_db? Simpler: do clock tests BEFORE register rate limit test.
        pass

    # ===== Second client for clock tests with fresh rate-limit stores =====
    # But in-memory stores are module-level; new client in same process shares them.
    # Reset in-memory stores manually by importing from auth (register store lives there)
    from app.routers.auth import _register_attempts
    from app.rate_limiter import _pin_limits, _nfc_limits, _qr_limits, _pin_failures, _pin_blocks
    _register_attempts.clear(); _pin_limits.clear(); _nfc_limits.clear(); _qr_limits.clear(); _pin_failures.clear(); _pin_blocks.clear()

    async with httpx.AsyncClient(transport=transport, base_url=BASE) as c2:
        # PIN test
        r = await c2.post("/auth/register", json={
            "restaurant_name": f"PINRest{uid_base}",
            "owner_name": "PIN",
            "email": f"pin{uid_base}@example.com",
            "password": "pinpass123",
        })
        print("PIN register:", r.status_code, r.text[:120])
        if r.status_code == 201:
            token = r.json()["access_token"]
            tenant_id = r.json()["tenant_id"]
            r2 = await c2.post("/employees", headers={"Authorization": f"Bearer {token}"}, json={
                "name": "PIN Emp", "pin": "9876", "clock_method": "pin"
            })
            print("PIN employee create:", r2.status_code, r2.text[:120])
            codes = []
            for i in range(15):
                rr = await c2.post("/clock", json={"tenant_id": tenant_id, "pin": "9876", "type": "in"})
                codes.append(rr.status_code)
                if i == 0:
                    print("First PIN clock:", rr.status_code, rr.text[:80])
            print("PIN clock codes:", codes)
            record("PIN clock rate limit 429", 429 in codes, f"codes={codes[:12]}...")
        else:
            record("PIN clock rate limit 429", False, f"register failed {r.status_code}")

        # NFC test
        from app.routers.auth import _register_attempts as _reg2
        from app.rate_limiter import _nfc_limits as _nfc2, _pin_limits as _pin2
        _reg2.clear(); _nfc2.clear(); _pin2.clear()
        r = await c2.post("/auth/register", json={
            "restaurant_name": f"NFCRest{uid_base}",
            "owner_name": "NFC",
            "email": f"nfc{uid_base}@example.com",
            "password": "nfcpass123",
        })
        print("NFC register:", r.status_code, r.text[:120])
        if r.status_code == 201:
            token = r.json()["access_token"]
            tenant_id = r.json()["tenant_id"]
            await c2.post("/employees", headers={"Authorization": f"Bearer {token}"}, json={
                "name": "NFC Emp", "pin": "1234", "nfc_uid": "A1B2C3D4", "clock_method": "nfc"
            })
            codes = []
            for i in range(15):
                rr = await c2.post("/clock/nfc", json={"tenant_id": tenant_id, "nfc_uid": "A1B2C3D4"})
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
