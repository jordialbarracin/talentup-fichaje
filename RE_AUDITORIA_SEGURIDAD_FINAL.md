"""
TalentUP Fichaje — Security re-audit report.
Score anterior: 76/100. Score actual: 84/100.
Tests: 64/64 passed.
"""

# Re-auditoría de Seguridad — TalentUP Fichaje

**Fecha:** 2026-07-20  
**Auditor:** Seguridad Senior (subagente)  
**Score anterior:** 76/100  
**Score seguridad actualizado:** 84/100  
**Diferencia:** +8 puntos  
**Tests:** 64/64 pasan

---

## 1. Verificación punto por punto

| Control | Estado | Evidencia / Notas |
|---|---|---|
| **JWT httpOnly cookies** | ✅ Funcional | `backend/app/routers/auth.py` setea `access_token` y `refresh_token` como **httpOnly, Secure, SameSite=Lax**. `backend/app/auth.py` ahora lee primero la cookie y usa header como fallback. Frontend usa `credentials: 'include'` y `getCookie('access_token')` para iniciar sesión. |
| **PIN_HASH_SALT** | ✅ Obligatorio | `backend/app/auth.py` exige `PIN_HASH_SALT` siempre (no solo en prod). Evita salt por defecto en cualquier entorno. |
| **PIN blocks Redis** | ✅ Sí | `backend/app/rate_limiter.py` implementa bloqueo de PIN con Redis y fallback en memoria. En producción `REDIS_URL` es obligatoria. |
| **CSP nonce** | ✅ Sí | `backend/app/main.py` genera nonce por request y lo inyecta en `Content-Security-Policy`. `style-src 'unsafe-inline'` residual. |
| **Body limit** | ✅ Sí | `MAX_BODY_SIZE = 1 MB`. Rechaza bodies > 1 MB con **413**. |
| **XSS (stored)** | ✅ Corregido | `POST /api/auth/register` ahora escapa `owner_name` y `restaurant_name` con `html.escape`. Prueba manual devuelve entidades HTML (`&lt;script&gt;`). |
| **SQLi** | ✅ Sí | Login y búsquedas usan ORM parametrizado. Prueba manual devuelve **401**. |
| **Rate limiting clock** | ✅ Sí | PIN/NFC/QR limitados a 10/min y bloqueo tras 5 fallos. Pruebas manuales devuelven **429**. |
| **Stripe webhook** | ⚠️ Parcial | Con `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET` configurados, sin firma devuelve **403** y firma falsa **400**. Sin Stripe configurado devuelve **503**, lo cual no es fail-closed ideal. |

---

## 2. Score detallado por área (0-100)

| Área | Score | Comentario |
|---|---|---|
| Autenticación JWT + cookies | 85 | Cookies httpOnly son ahora el canal funcional (cookie first). Frontend aún lee `access_token` del JSON de login, aunque no lo persiste en localStorage. |
| PIN salt + hashing | 90 | `PIN_HASH_SALT` obligatorio; SHA256 first-pass + bcrypt verify. |
| Rate limiting / PIN block | 85 | Redis correcto; registro de usuario limitado a 3/h. |
| CSP / Headers de seguridad | 80 | CSP nonce, HSTS, X-Frame, XCTO. `style-src 'unsafe-inline'` residual. |
| Input validation / XSS | 85 | Register y employees escapan HTML. Tenant.name/User.name devuelven entidades. |
| SQLi / IDOR / multi-tenant | 95 | ORM parametrizado, aislamiento de tenant verificado. |
| Body size / DoS básico | 95 | Límite de 1 MB funciona. |
| Stripe webhook | 75 | Fail-closed cuando está configurado; 503 si falta Stripe es aceptable en dev pero no ideal en prod. |
| **Seguridad global** | **84** | Subió del 76 gracias a cookies funcionales, XSS corregido y PIN salt obligatorio. |

---

## 3. Hallazgos y recomendaciones

### 🟡 MEDIO: Stripe webhook sin secret config → 503 (no fail-closed)

- Con `STRIPE_SECRET_KEY` vacío el endpoint devuelve **503**.
- **Recomendación:** En producción, si `STRIPE_WEBHOOK_SECRET` falta, devolver **403** en lugar de 503, para evitar que un atacante descubra que Stripe no está configurado o para forzar fail-closed.

### 🟢 BAJO: `style-src 'unsafe-inline'` en CSP

- Necesario para frontend vanilla. Riesgo residual aceptable a corto plazo.

### 🟢 BAJO: OpenAPI expuesto (`/docs`, `/openapi.json`)

- Devuelven 200. Considerar deshabilitar en producción o proteger con autenticación.

---

## 4. Conclusión

**Sí, el score de seguridad subió: de 76 a 84 (+8 puntos).**

Las mejoras reales son:
- Cookies httpOnly implementadas **y consumidas** por el backend.
- `PIN_HASH_SALT` obligatorio en todos los entornos.
- CSP nonce por request.
- Body limit de 1 MB funcional.
- Rate limiting de clock con 429 correcto.
- Stripe webhook verifica firma cuando está configurado.
- **XSS en `/api/auth/register` corregido** aplicando `html.escape()` a `owner_name` y `restaurant_name`.

---

## 5. Evidencia ejecutada

- `pytest -v` → **64 passed**.
- `curl -I http://localhost:8000/api/health` → CSP con nonce, HSTS, X-Frame, XCTO.
- POST `/api/auth/login` con body >1 MB → **413**.
- POST `/api/auth/register` con `owner_name: <script>alert(1)</script>` → devuelve `&lt;script&gt;alert(1)&lt;/script&gt;`.
- POST `/api/auth/login` con SQLi → **401**.
- GET `/api/employees` con JWT manipulado → **401**.
- 12× POST `/api/clock/nfc` → 10×201 + 2×429.
- 8× POST `/api/clock` con PIN erróneo → 429 tras bloqueo.
- POST `/api/billing/webhook` sin firma con Stripe configurado → **403**; firma falsa → **400**.

---

**Score final seguridad: 84/100. Subió del 76.**
