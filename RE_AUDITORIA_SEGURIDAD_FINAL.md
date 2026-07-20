# Re-auditoría de Seguridad — TalentUP Fichaje FINAL

**Fecha:** 2026-07-20  
**Auditor:** Seguridad Senior (subagente)  
**Score anterior:** 76/100  
**Score seguridad actualizado:** 80/100  
**Diferencia:** +4 puntos  
**Tests:** 64/64 pasan (117 s)

---

## 1. Verificación punto por punto

| Control | Estado | Evidencia / Notas |
|---|---|---|
| **JWT httpOnly cookies** | ✅ Parcial | `backend/app/routers/auth.py:138-153` y `:329-344` setean `access_token` y `refresh_token` como **httpOnly, Secure, SameSite=Lax**. Sin embargo, `GET /api/auth/me` no lee la cookie: usa únicamente `Authorization: Bearer`. Las cookies existen pero no son el mecanismo funcional de auth. |
| **PIN blocks Redis** | ✅ Sí | `backend/app/rate_limiter.py:126-187` implementa bloqueo de PIN con `pin:block:{key}` en Redis (TTL 5 min) con fallback en memoria. `backend/app/routers/clock.py:185-225` consume `is_pin_blocked` / `record_pin_failure`. En producción `REDIS_URL` es obligatoria (`main.py:71-74`). |
| **CSP nonce** | ✅ Sí | `backend/app/main.py:104-140` genera nonce por request y lo inyecta en `Content-Security-Policy`. Penalización menor: `style-src 'self' 'unsafe-inline'` sigue permitido. |
| **Body limit** | ✅ Sí | `MAX_BODY_SIZE = 1 MB`. Tanto `BodySizeLimitMiddleware` como `@app.middleware("http")` rechazan bodies > 1 MB con **413**. Confirmado con curl y tests. |
| **XSS (stored)** | ❌ **Falla real** | `POST /api/auth/register` NO escapa `owner_name` ni `restaurant_name`. Prueba manual: enviar `"owner_name":"<script>alert(1)</script>"` devuelve el script literal en `user.name`. Los tests de XSS solo cubren `POST /api/employees`, no el registro. |
| **SQLi** | ✅ Sí | Login y búsquedas usan ORM parametrizado. Prueba manual con `' OR '1'='1` devuelve **401**. Tests pasan. |
| **Rate limiting clock** | ✅ Sí | PIN/NFC/QR limitados a 10/min y bloqueo tras 5 fallos. Prueba manual: 10 success + 429, 4×401 + 429 en PIN erróneo. |
| **Stripe webhook** | ✅ Parcial | Con `STRIPE_SECRET_KEY` configurado, sin firma devuelve **403** y firma falsa **400**. Sin Stripe configurado devuelve **503** (aceptable en dev, peligroso en prod si se olvida la variable). |

---

## 2. Score detallado por área (0-100)

| Área | Score | Comentario |
|---|---|---|
| Autenticación JWT + cookies | 75 | Cookies httpOnly presentes pero no se consumen como mecanismo principal; frontend sigue con Bearer/localStorage. |
| Rate limiting / PIN block | 85 | Implementación Redis correcta; registro de usuario limitado a 3/h in-memory. |
| CSP / Headers de seguridad | 80 | Buen CSP nonce, HSTS, X-Frame, XCTO. `style-src 'unsafe-inline'` residual. |
| Input validation / XSS | 55 | **Stored XSS en `/api/auth/register`** por no escapar `owner_name`/`restaurant_name`. Empleados sí escapan con `html.escape`. |
| SQLi / IDOR / multi-tenant | 95 | ORM parametrizado, aislamiento de tenant verificado, IDOR rechazado. |
| Body size / DoS básico | 95 | Límite de 1 MB funciona. |
| Stripe webhook | 75 | Verificación de firma presente; cae a 503 si Stripe no está configurado. |
| **Seguridad global** | **80** | Subió del 76, pero el XSS en registro es un hallazgo crítico que frena el ascenso. |

---

## 3. Hallazgos críticos y recomendaciones

### 🔴 CRÍTICO: Stored XSS en registro de tenant (`/api/auth/register`)

- **Archivo:** `backend/app/routers/auth.py:232-252`
- **Impacto:** Un atacante puede registrar un restaurante con nombre o nombre de propietario malicioso y el script se almacena y devuelve en la respuesta JSON. Si el frontend renderiza ese valor como HTML, se ejecuta JS.
- **Fix:** Aplicar `html.escape()` a `req.restaurant_name` y `req.owner_name` antes de guardar, o al devolver `user.to_dict()` / `tenant.to_dict()`. Reutilizar el patrón ya usado en `employees.py`.
- **Esfuerzo:** 0.25 días.

### 🟡 MEDIO: Cookies httpOnly no son mecanismo funcional de autenticación

- `get_current_user` en `backend/app/auth.py:101-125` solo lee `Authorization: Bearer`. El endpoint `/api/auth/me` no lee `access_token` de la cookie.
- **Fix:** Añadir lector de cookie en `get_current_user` (fallback: cookie → header) para que las cookies httpOnly sean efectivas.

### 🟡 MEDIO: Body size middleware duplicado

- `BodySizeLimitMiddleware` y `@app.middleware("http")` hacen lo mismo. Mantener uno solo para evitar doble-consumo del body.

### 🟢 BAJO: `style-src 'unsafe-inline'` en CSP

- Necesario para frontend vanilla. Riesgo residual aceptable a corto plazo.

### 🟢 BAJO: JWT_SECRET aleatorio en dev

- `backend/app/auth.py:25-34` genera secret aleatorio si `JWT_SECRET` no está. Documentado como advertencia; operacionalmente debe forzarse en prod.

---

## 4. Conclusión

**Sí, el score de seguridad subió: de 76 a 80 (+4 puntos).**

Las mejoras reales son:
- Cookies httpOnly implementadas (aunque no consumidas).
- PIN blocks con Redis implementados y consumidos por el router de fichaje.
- CSP nonce por request.
- Body limit de 1 MB funcional.
- Rate limiting de clock con 429 correcto.
- Stripe webhook con verificación de firma.

**El techo no sube más porque existe un stored XSS activo en `/api/auth/register`** y las cookies httpOnly aún no son el canal funcional de autenticación. Corregir el XSS y hacer que `/api/auth/me` lea la cookie elevaría el score a **85-87**.

---

## 5. Evidencia ejecutada

- `pytest -q` → **64 passed**.
- `curl -I http://localhost:8000/api/health` → CSP con nonce presente, HSTS, X-Frame, XCTO.
- POST `/api/auth/login` con body >1 MB → **413**.
- POST `/api/auth/register` con `owner_name: <script>alert(1)</script>` → devuelve el script literal (XSS confirmado).
- POST `/api/auth/login` con SQLi → **401**.
- GET `/api/auth/me` con JWT manipulado → **401**.
- 15× POST `/api/clock/nfc` → 10×201 + 5×429.
- 15× POST `/api/clock` con PIN erróneo → 4×401 + 11×429.
- POST `/api/billing/webhook` sin firma con Stripe configurado → **403**; firma falsa → **400**.

---

**Score final seguridad: 80/100. Subió del 76, pero el XSS en registro debe corregirse antes de considerar el producto apto para producción pública.**
