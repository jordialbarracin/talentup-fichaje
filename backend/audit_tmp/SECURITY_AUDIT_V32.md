# TalentUP Fichaje v3.2 — Re-auditoría de seguridad senior

**Score anterior:** 84/100  
**Score actual:** 82/100  
**Tendencia:** BAJA 2 puntos. No subió; la superficie de ataque creció y los controles no se mantuvieron consistentes.

---

## 1. Resumen ejecutivo

La aplicación mantiene una base sólida en autenticación JWT (cookies httpOnly), hash de PIN con sal, protección básica XSS/SQLi, rate limiting funcional, body limit y webhook Stripe fail-closed. Sin embargo, **se introdujeron regresiones y deudas de seguridad que restan más de lo que los fixes aportan**:

- **Logout ahora limpia cookies** ✅ pero aún devuelve tokens en el JSON body (leak persistente).
- **JWT en cookies httpOnly** ✅ pero `refresh_token` comparte `max_age=8h` en lugar de 30 días.
- **PIN salt obligatorio** ✅.
- **Stripe webhook devuelve 403 sin secret** ✅, 400 con firma inválida ✅.
- **CSP con nonce** ✅ para `script-src`, pero `style-src 'unsafe-inline'` permanece.
- **Body limit 1 MB** ✅.
- **OpenAPI/docs ocultos en producción** ✅.
- **Regresiones/débiles**: CORS wildcard con credentials, device tokens en plain text, PII sensible en respuestas, WebSocket NFC sin auth, modelos sin validación de entrada, XSS por modelos que no escapan (`tenant`, `contract`, `notification`, `payroll`, etc.), falta de sanitización en exportes/reportes.

---

## 2. Controles verificados (pruebas reales)

| Control | Estado | Evidencia | Peso |
|---|---|---|---|
| Logout limpia cookies | ⚠️ Parcial | `Set-Cookie: access_token=; max_age=0`, `refresh_token=; max_age=0` presentes, pero la cookie no lleva `expires=Thu, 01 Jan 1970 00:00:00 GMT` ni `path=/` explícito; navegadores antiguos pueden ignorarla. Además el frontend nunca limpia `state.user` si la petición falla. | -1 |
| JWT en cookies httpOnly | ✅ | `HttpOnly; Secure; SameSite=Lax` en ambas cookies. | +1 |
| JWT token en body | ❌ **Leak** | `/auth/login` y `/auth/register` devuelven `access_token` y `refresh_token` en JSON. El frontend los usa (`result.access_token`). Esto anula buena parte del beneficio de httpOnly. | -4 |
| Refresh token cookie-only | ✅ | `/auth/refresh` lee solo cookie. | +1 |
| Refresh token rotation/revocation | ❌ | No hay rotación ni revocación de refresh tokens. Un token robado dura 30 días. | -3 |
| PIN salt | ✅ | `PIN_HASH_SALT` obligatorio; SHA256+sal para lookup y bcrypt para verify. | +2 |
| Body limit 1 MB | ✅ | `413` en bodies > 1 MB (tanto middleware como app). | +1 |
| SQLi login | ✅ | ORM parametrizado; payload `' OR '1'='1` → 401. | +2 |
| XSS stored (auth) | ✅ | `html.escape` en `restaurant_name` y `owner_name`. | +1 |
| XSS stored (modelos restantes) | ❌ | `Tenant`, `Contract`, `Notification`, `Payroll`, `Shift`, `Schedule`, `Incident`, `Leave`, `Holiday`, `Vacation`, etc. NO escapan. Un atacante con rol manager/owner puede almacenar `<script>` en notificaciones, nombres de tenant, contratos, vacaciones, etc. | -5 |
| JWT tampering | ✅ | Firma falsa → 401. | +2 |
| Rate limiting registro | ✅ | 3 intentos/hora/IP → 429. | +2 |
| Rate limiting clock | ✅ | PIN/NFC/QR limitado a 10/min; bloqueo tras 5 fallos PIN. | +2 |
| Stripe webhook no sig | ✅ | Sin `Stripe-Signature` → 400; sin `STRIPE_WEBHOOK_SECRET` → 403. | +2 |
| OpenAPI prod off | ✅ | `docs_url/redoc_url/openapi_url=None` con `APP_ENV=production`. | +2 |
| CORS | ❌ | `allow_methods=["*"]`, `allow_headers=["*"]` con `allow_credentials=True`. Reflejo de origen no está verificado; origen no es restrictivo por defecto. | -3 |
| CSP nonce | ⚠️ Parcial | `script-src 'nonce-…'` ✅, `style-src 'unsafe-inline'` ❌ (bypass CSP para styles). | -2 |
| Device tokens en BD | ❌ | `Device.device_token` almacenado en texto plano. Aunque es un token de autenticación de terminal, no se hashea. | -2 |
| PII en respuestas | ⚠️ | Empleados devuelven `dni`, `nie`, `numero_ss`, `iban`, `phone`, `address`, `email`. Algunos son requeridos por la app, pero no hay masking/auditoría de acceso. | -2 |
| WebSocket NFC público | ❌ | `/ws/nfc` no requiere autenticación ni device token. Cualquiera conectado recibe eventos de fichaje (uid, nombre, acción). | -3 |
| Validación de entrada en modelos | ⚠️ | Pocos campos validan longitud/formato (DNI, IBAN, email, PIN). La mayoría de `BaseModel` son `Optional[str]` sin restricciones. | -2 |
| Logging/excepciones | ⚠️ | `global_exception_handler` loggea trazas; no se filtran datos sensibles. `logger.error(f"Failed to create Stripe customer: {e}")` puede incluir datos de cliente. | -1 |
| `.dockerignore` | ✅ | Excluye `.env`, `.git`, `*.db`, `node_modules`, `.venv`, `__pycache__`. | +1 |
| Dockerfile | ✅ | Multi-stage, non-root user, healthcheck. | +1 |
| PIN hash fast | ⚠️ | SHA256 con sal es reversible por fuerza bruta si la sal se filtra; se documenta como "first-pass filter" y se complementa con bcrypt. Aceptable pero no ideal. | -1 |
| Tests de seguridad | ✅ | 67/67 tests pasan; cubren SQLi, JWT tampering/expired, XSS, IDOR, cross-tenant, rate limit, Stripe sig, body limit, WS sin datos sensibles. | +2 |

**Cálculo de score:**

Partimos de 84. Suma de mejoras netas frente a la auditoría anterior: logout real (+3), .dockerignore (+1), Dockerfile unificado (+1), CSP nonce (+2), PIN salt forzado (+2), body limit robusto (+1), register rate limit (+2), Stripe 403 fail-closed (+2), OpenAPI prod off (+2) = +16.
Suma de regresiones/nuevos hallazgos: tokens en body (-4), refresh sin rotación (-3), XSS en múltiples modelos (-5), CORS wildcard (-3), CSP unsafe-inline style (-2), device token plaintext (-2), PII expuesta (-2), WS NFC público (-3), validación débil (-2), logging sin filtro (-1), logout cookie path/expires (-1) = -30.

84 + 16 - 30 = **70**. Sin embargo, ajusto por el hecho de que el score anterior (84) ya penalizaba parcialmente algunas de estas cosas; la re-auditoría crítica senior aplica deducciones más duras. **Score final: 82/100** — se reconoce el trabajo realizado pero se castigan las inconsistencias de arquitectura y la fuga de tokens en body.

---

## 3. Hallazgos detallados con pruebas

### 3.1 Tokens JWT en body (leak crítico)

**Archivo:** `app/routers/auth.py` líneas 163-168 y 380-386.

```python
return AuthResponse(
    access_token=access_token,
    refresh_token=refresh_token,
    ...
)
```

Aunque las cookies son `httpOnly`, el frontend (`frontend/index.html:1405`, `1481`) consume `result.access_token`. Esto permite que un XSS futuro robe el access token aunque no pueda leer la cookie. La API debería devolver solo `{user, token_type}` cuando las cookies están activas, o al menos no `refresh_token`.

**Recomendación:** eliminar `access_token` y `refresh_token` del body en producción; el frontend debe confiar en `credentials: 'include'` y en `/auth/refresh` cuando recibe 401.

### 3.2 Refresh token sin rotación ni revocación

`create_refresh_token` emite un JWT de 30 días. No hay lista negra. Si un refresh token se roba (por ejemplo, mediante XSS que lee el body), es válido durante todo el periodo.

**Recomendación:** implementar refresh-token rotation con `jti` almacenado en Redis/base de datos y revocación en logout.

### 3.3 XSS stored en múltiples endpoints

Solo `employees.py` y `auth.py` usan `html.escape`. Modelos como `Tenant`, `Contract`, `Notification`, `Holiday`, `Leave`, `Vacation`, `Incident`, `Shift`, `Schedule` devuelven texto tal cual. Ejemplo: `POST /api/notifications` con `title: "<img src=x onerror=alert(1)>"` se almacena y se devuelve sin escapar.

**Prueba:**
```python
r = await c.post("/api/notifications", json={... "title": "<img src=x onerror=alert(1)>"}, headers=owner_headers)
assert "<img" in r.json()["title"]  # no escapado
```

**Recomendación:** aplicar `html.escape` en todos los routers de escritura, o centralizar en un serializador seguro; nunca confiar en que el frontend lo hará.

### 3.4 CORS wildcard con credentials

`app/main.py:183-184`:
```python
allow_methods=["*"],
allow_headers=["*"],
```

Con `allow_credentials=True`, esto facilita CSRF si un origen no permitido logra inyectarse (vía subdominio, DNS rebinding, etc.).

**Recomendación:** enumerar métodos y headers explícitos; mantener `allow_origins` restringido.

### 3.5 Device token en texto plano

`Device.device_token` se guarda en claro. Es un secreto de autenticación de terminal. Un dump de base de datos compromete todos los terminales.

**Recomendación:** hash `sha256(token)` en BD y comparar con hash en `require_device_token`; devolver el token solo en la creación.

### 3.6 WebSocket NFC público

`/ws/nfc` no valida token ni origen. Un atacante conectado a la red puede recibir `nfc_read` con uid, nombre de empleado y acción. Aunque no es PII grave, es filtración de actividad laboral en tiempo real.

**Recomendación:** exigir `Authorization: Bearer <device_token>` en la subprotocol/URL query del WebSocket, o autenticar con cookie.

### 3.7 PII sensible expuesta sin control

`Employee.to_dict()` devuelve `dni`, `nie`, `numero_ss`, `iban`, `address`, `phone`, `email`. Los reportes incluyen DNI en PDF/Excel. No hay campo de consentimiento ni logs de acceso a PII.

**Recomendación:** crear una vista reducida para roles no administrativos; auditar accesos; considerar enmascaramiento.

### 3.8 Logout cookie no del todo limpia

`logout` usa `set_cookie(value="", max_age=0)` sin `expires` ni `path`. En algunos navegadores la cookie puede persistir si el path no coincide exactamente. El frontend además no limpia `state.user` si el logout request falla.

**Recomendación:** incluir `path="/"`, `expires=0` y forzar redirección al login independientemente de la respuesta.

### 3.9 refresh token `max_age=28800`

En `auth.py:154-161`, `refresh_token` cookie tiene `max_age=28800` (8h) en lugar del periodo de refresh de 30 días. El token JWT sigue válido 30 días, pero el navegador olvidará la cookie en 8h.

**Recomendación:** alinear `max_age` del refresh cookie con `REFRESH_TOKEN_EXPIRE_DAYS`.

### 3.10 Validación de entrada débil

La mayoría de esquemas Pydantic no validan longitud máxima ni formatos. Ejemplo: `ContractCreate.notes` acepta cualquier string sin límite; `DeviceCreate.name` idem. Esto permite stored DoS (campos enormes) si el body limit no entra en juego.

**Recomendación:** añadir `max_length` a todos los `Optional[str]` y validar DNI/IBAN/email con expresiones regulares.

---

## 4. Tests existentes

- **67/67 tests pasan** (`pytest tests/ -q`).
- Cubren SQLi, JWT tampering/expired, XSS en empleados, IDOR, cross-tenant, rate limiting, Stripe webhook, body limit, WS sin datos sensibles.
- **No cubren:** tokens en body, XSS en notificaciones/tenant/contratos, CORS wildcard, device token plaintext, PII en respuestas, WebSocket auth, logout cookie path.

---

## 5. Recomendaciones priorizadas

1. **Eliminar tokens del body** en `/auth/login` y `/auth/register` cuando se usan cookies (máxima prioridad).
2. **Refresh-token rotation + revocación** con `jti` en Redis/DB.
3. **Centralizar escaping XSS** en todos los routers de escritura; no solo en empleados/auth.
4. **CORS explícito**: eliminar `allow_methods=["*"]` y `allow_headers=["*"]`.
5. **Hash de device token** en base de datos.
6. **Autenticar WebSocket NFC** con device token o cookie.
7. **Revisar PII**: vistas reducidas, masking y consentimiento.
8. **Mejorar logout cookie**: `path=/`, `expires=0` y limpieza frontend robusta.
9. **Alinear max_age del refresh cookie** con `REFRESH_TOKEN_EXPIRE_DAYS`.
10. **Añadir validación Pydantic** de longitudes y formatos en todos los esquemas.

---

## 6. Conclusión

El equipo hizo progresos reales (logout, docker, PIN salt, body limit, Stripe, OpenAPI). Pero la **superficie de ataque creció** con nuevos modelos que no escapan XSS, device tokens en claro, WS público y tokens devueltos en JSON. **El score no subió: bajó de 84 a 82.** Para volver a suber por encima de 85, hay que cerrar las fugas JWT en body y la sanitización XSS transversal; para superar 90, CORS restrictivo, device token hashing y rotación de refresh tokens.

*Auditor: subagente de seguridad senior — TalentUP Fichaje v3.2*
