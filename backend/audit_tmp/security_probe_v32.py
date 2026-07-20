"""
TalentUP Fichaje v3.2 — Auditoría de seguridad black-box + code review.
Proceso interno: 0-100. Crítico. Guarda hallazgos en audit_tmp/SECURITY_AUDIT_V32.md.
"""
import os, sys, json, base64, hmac, hashlib, time, importlib

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./audit_tmp/audit_v32.db"
os.environ.setdefault("PIN_HASH_SALT", "audit-salt-32-bytes-long-value")
os.environ.setdefault("JWT_SECRET", "audit-jwt-secret-32-bytes-long-value")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy_for_audit")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_webhook_secret_32bytes_long")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from app.main import app
from app.database import init_db
from app.routers.auth import _register_attempts
from app.rate_limiter import _pin_limits, _nfc_limits, _qr_limits, _pin_failures, _pin_blocks

BASE = "http://test/api"


def parse_set_cookie(set_cookie):
    cookies = {}
    if not set_cookie:
        return cookies
    for part in set_cookie.split(","):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k] = v.split(";")[0]
    return cookies


def cookie_jar(cookies):
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


async def run():
    db_path = "./audit_tmp/audit_v32.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    await init_db()
    _register_attempts.clear()
    _pin_limits.clear(); _nfc_limits.clear(); _qr_limits.clear()
    _pin_failures.clear(); _pin_blocks.clear()

    transport = httpx.ASGITransport(app=app)
    results = {}
    async with httpx.AsyncClient(transport=transport, base_url=BASE) as c:
        uid = str(int(time.time()))

        # 1. Logout limpia cookies
        r = await c.post("/auth/register", json={
            "restaurant_name": f"Logout{uid}",
            "owner_name": "Logout",
            "email": f"logout{uid}@example.com",
            "password": "logoutpass123",
        })
        cookies = parse_set_cookie(r.headers.get("set-cookie", ""))
        r2 = await c.post("/auth/logout", headers={"Cookie": cookie_jar(cookies)})
        set_cookie = r2.headers.get("set-cookie", "")
        results["logout_clears_cookies"] = (r2.status_code == 200 and
                                            "access_token=;" in set_cookie and
                                            "refresh_token=;" in set_cookie)

        # 2. JWT httpOnly cookie vs body
        results["jwt_cookie_httponly"] = "access_token=" in r.headers.get("set-cookie", "") and "HttpOnly" in r.headers.get("set-cookie", "")
        results["jwt_body_leak"] = "access_token" in r.json() and r.json().get("access_token") is not None

        # 3. /auth/me con cookie
        me = await c.get("/auth/me", headers={"Cookie": cookie_jar(cookies)})
        results["me_with_cookie_before_logout"] = me.status_code == 200
        me_after = await c.get("/auth/me", headers={"Cookie": cookie_jar(parse_set_cookie(set_cookie))})
        results["me_after_logout_401"] = me_after.status_code == 401

        # 4. Body limit (1 MB)
        big = {"payload": "a" * (1024 * 1100)}
        rbl = await c.post("/auth/login", json=big)
        results["body_limit_413"] = rbl.status_code == 413

        # 5. XSS stored en registro
        r = await c.post("/auth/register", json={
            "restaurant_name": f"XSSTest{uid}",
            "owner_name": "<script>alert(1)</script>",
            "email": f"xss{uid}@example.com",
            "password": "xsspass123",
        })
        owner_name = r.json()["user"]["name"]
        results["xss_register_escaped"] = "<script>" not in owner_name and "</script>" not in owner_name and "alert(1)" in owner_name

        # 6. SQLi login
        r = await c.post("/auth/login", json={"email": "admin@example.com' OR '1'='1", "password": "x"})
        results["sqli_login_401"] = r.status_code == 401

        # 7. JWT tampering
        token = r.json().get("access_token") if r.status_code == 200 else ""
        if not token:
            r = await c.post("/auth/register", json={
                "restaurant_name": f"JWTTest{uid}",
                "owner_name": "JWT",
                "email": f"jwt{uid}@example.com",
                "password": "jwtpass123",
            })
            token = r.json()["access_token"]
        h, p, s = token.split(".")
        payload = json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)).decode())
        fake_p = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        fake_s = base64.urlsafe_b64encode(hmac.new(b"fake", f"{h}.{fake_p}".encode(), hashlib.sha256).digest()).decode().rstrip("=")
        fake = f"{h}.{fake_p}.{fake_s}"
        r = await c.get("/auth/me", headers={"Authorization": f"Bearer {fake}"})
        results["jwt_tamper_401"] = r.status_code == 401

        # 8. Stripe webhook fail-closed (no secret configured)
        # Con STRIPE_WEBHOOK_SECRET set, sin firma → 400 (correcto). Sin secret → 403.
        r = await c.post("/billing/webhook", json={"type": "checkout.session.completed"})
        results["stripe_no_sig_400_or_403"] = r.status_code in (400, 403)

        # 9. Register rate limit
        _register_attempts.clear()
        codes = []
        for i in range(5):
            rr = await c.post("/auth/register", json={
                "restaurant_name": f"RL{i}",
                "owner_name": "RL",
                "email": f"rl{uid}_{i}@example.com",
                "password": "rlpass123",
            })
            codes.append(rr.status_code)
        results["register_rate_limit_429"] = 429 in codes or codes.count(201) <= 3
        results["register_codes"] = codes

        # 10. OpenAPI prod off (reload con APP_ENV=production)
        # Se prueba en subproceso aparte.

        # 11. CSP nonce en health
        r = await c.get("/health")
        csp = r.headers.get("content-security-policy", "")
        results["csp_present"] = bool(csp)
        results["csp_nonce"] = "nonce-" in csp
        results["csp_unsafe_inline_script"] = "'unsafe-inline'" in csp.split("script-src")[1].split(";")[0] if "script-src" in csp else False
        results["csp_unsafe_inline_style"] = "'unsafe-inline'" in csp.split("style-src")[1].split(";")[0] if "style-src" in csp else False

        # 12. CORS allow_methods=* / allow_headers=* con credentials
        results["cors_methods_star"] = True  # revisado en main.py
        results["cors_headers_star"] = True

    return results


if __name__ == "__main__":
    import asyncio
    res = asyncio.run(run())
    print(json.dumps(res, indent=2, default=str))
