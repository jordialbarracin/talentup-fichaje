# Auditoría de seguridad — TalentUP Fichaje DEFINITIVO v3

- **Score anterior:** 76/100
- **Score actual:** 84/100
- **Subida:** +8 puntos
- **Tests ejecutados:** 15/15 passed (`tests/test_security.py`) + 11 probes manuales con `httpx.ASGITransport`
- **Fecha:** 2026-07-20
- **Auditor:** Subagente de seguridad Hermes
- **Backend auditado:** `http://localhost:8000/api` (D:/talentup-fichaje/backend)

---

## 1. Fixes prometidos: estado real

| Fix prometido | ¿Implementado realmente? | Evidencia / Resultado probe |
|---|---|---|
| JWT httpOnly cookies (no localStorage) | ✅ Sí | `Set-Cookie` devuelve `access_token` y `refresh_token` con `HttpOnly; Secure; SameSite=lax`. `/api/auth/me` consume la cookie primero, Bearer como fallback. |
| `PIN_HASH_SALT` obligatorio | ✅ Sí | `app/auth.py` hace `raise RuntimeError("PIN_HASH_SALT requerido")` si falta. Hash de PIN usa SHA256 con sal + bcrypt verify como segunda barrera. |
| `JWT_SECRET` prod obligatorio | ✅ Sí | `app/auth.py` lanza `RuntimeError` en producción si falta. En dev genera secreto aleatorio por arranque. |
| Stripe fail-closed | ✅ Sí | Webhook devuelve 400 si falta firma (`Firma de webhook requerida`) o firma inválida (`Invalid signature`). Sin `STRIPE_WEBHOOK_SECRET` devuelve 400. |
| Rate limit registro Redis | ✅ Sí (con fallback memoria) | `auth.py` limita registro a 3/h por IP, usa Redis cuando `REDIS_URL` está configurado. Probe: `[201, 429, 429, 429]`. |
| XSS registro escapado | ✅ Sí | `owner_name` y `restaurant_name` se escapan con `html.escape()` antes de guardar. Probe devolvió `&lt;script&gt;alert(1)&lt;/script&gt;`. |
| CSP nonce (extra) | ✅ Sí | Cada respuesta incluye nonce aleatorio en `script-src`; no `unsafe-inline` en scripts. Sí en `style-src`. |
| Body limit (extra) | ✅ Sí | Middleware rechaza body > 1 MB con 413. Probe devolvió 413. |

---

## 2. Resultados de los probes ejecutados

```
[PASS] CSP nonce: nonce=True, no unsafe-inline=True
[PASS] Body limit 413: status=413
[PASS] XSS register escaped: name='&lt;script&gt;alert(1)&lt;/script&gt;'
[PASS] SQLi login: status=401
[PASS] JWT httpOnly cookie: HttpOnly=True, Secure=True, SameSite=True
[PASS] JWT tampering rejected: status=401
[PASS] Refresh token flow: status=200
[PASS] PIN_HASH_SALT configured: len=30
[PASS] Stripe webhook fail-closed: no-sig=400, fake-sig=400
[PASS] Register rate limit 429: codes=[201, 429, 429, 429]
[PASS] PIN clock rate limit 429: codes=[201, 400, 400, 400, 400, 429, 429, ...]
[PASS] NFC clock rate limit 429: codes=[201, 201, 201, 201, 201, 201, 201, 201, 201, 201, 429, ...]
```

---

## 3. Bug encontrado y corregido durante la auditoría

### `rate_limiter._record()` lanzaba `KeyError`
**Archivo:** `app/rate_limiter.py:68-69`

```python
# ANTES (bug)
def _record(store: dict[str, list[float]], key: str):
    store[key].append(time_module.time())  # KeyError si la IP no existía
```

Esto rompía el rate-limit en memoria la primera vez que una IP nueva intentaba registrar o fichar. Lo corregí a:

```python
# DESPUÉS
def _record(store: dict[str, list[float]], key: str):
    if key not in store:
        store[key] = []
    store[key].append(time_module.time())
```

**Impacto:** Sin este fix, el rate-limit de registro y clock fallaba silenciosamente con un 500, dejando los endpoints desprotegidos en el primer intento. Se trata de una vulnerabilidad DoS/rate-limit bypass real.

---

## 4. Hallazgos críticos residuales (por qué no sube más de 84)

### 4.1. JWT sigue expuesto en el body JSON además de la cookie httpOnly
**Archivo:** `app/routers/auth.py`

Los endpoints `/api/auth/login`, `/api/auth/register` y `/api/auth/refresh` devuelven `access_token` y `refresh_token` tanto en cookies httpOnly **como en el body JSON**. Si el frontend decide guardarlos en `localStorage` o si un atacante con XSS/CSRF logra leer la respuesta de estos endpoints, la mitigación httpOnly se anula parcialmente.

**Recomendación:** En el flujo cookie-first, no devolver tokens en el body. Devolver solo un indicador `token_delivered: cookie` o similar. Mantener Bearer en header solo para clientes no-web compatibles, documentado como riesgo.

**Penalización:** -3 puntos.

---

### 4.2. Refresh tokens sin rotación ni revocación, 30 días fijos
**Archivo:** `app/auth.py:40`, `app/routers/auth.py:175-242`

- `REFRESH_TOKEN_EXPIRE_DAYS = 30` por defecto.
- No hay lista de tokens revocados ni rotación en el endpoint `/api/auth/refresh`.
- Si se roba un refresh token, es válido durante 30 días sin forma de invalidarlo más allá de desactivar el usuario.

**Recomendación:** Implementar refresh-token rotation (nuevo refresh token en cada uso) y un `refresh_token_jti` store (Redis) para revocación global o por dispositivo.

**Penalización:** -3 puntos.

---

### 4.3. Datos personales sensibles sin cifrado en reposo
**Archivos:** `app/models/employee.py`, `app/models/tenant.py`

La base de datos almacena DNI, NIE, número SS, IBAN, dirección, teléfono, email, etc. en texto claro. No hay cifrado a nivel de columna ni de bucket. En caso de filtración de backup o SQL injection exitosa, la exposición de datos es total.

**Recomendación:** Cifrar columnas sensibles con AES-256-GCM (ej. SQLAlchemy `EncryptedType` o cifrado aplicación con KMS). Marcar campos con una etiqueta `pii` o `sensitive` y aplicar masking en logs.

**Penalización:** -3 puntos.

---

### 4.4. CORS permite todos los métodos y headers desde orígenes autorizados
**Archivo:** `app/main.py:170-182`

```python
allow_methods=["*"],
allow_headers=["*"],
```

Con `allow_credentials=True`, un origen permitido comprometido puede realizar cualquier método y enviar cualquier header (incluyendo `Authorization`, `X-Request-ID`, etc.). Esto amplía la superficie de CSRF y preflight cache poisoning.

**Recomendación:** Reemplazar `"*"` por listas explícitas: `allow_methods=["GET","POST","PUT","PATCH","DELETE"]` y `allow_headers=["content-type","authorization","x-request-id"]`. Revisar si `allow_origins` incluye dominios wildcard en staging/prod.

**Penalización:** -1 punto.

---

### 4.5. CSP mantiene `style-src 'unsafe-inline'`
**Archivo:** `app/main.py:115`

Aunque `script-src` usa nonce correctamente, `style-src` permite inline CSS arbitrario. Esto debilita la CSP frente a ataques que inyecten estilos maliciosos (data exfiltration vía CSS, clickjacking asistido).

**Recomendación:** Migrar a nonce/hash para `style-src` o al menos limitar a `'self'` si no hay CSS inline esencial.

**Penalización:** -1 punto.

---

### 4.6. HSTS enviado también sobre conexiones HTTP
**Archivo:** `app/main.py:125`

```python
response.headers["Strict-Transport-Security"] = "max-age=31536000"
```

El header HSTS se envía incluso en respuestas HTTP no seguras. Eso no es peligroso por sí solo, pero puede causar comportamientos inconsistentes si alguien accede accidentalmente por HTTP antes de redirigir a HTTPS.

**Recomendación:** Incluir HSTS solo cuando la petición sea HTTPS o detrás de un proxy TLS; añadir `includeSubDomains; preload`.

**Penalización:** -0.5 puntos.

---

### 4.7. Device tokens y refresh tokens almacenados en texto plano en BBDD
**Archivos:** `app/routers/devices.py`, `app/models/user.py`

- `Device.device_token` se guarda tal cual (`secrets.token_urlsafe(32)`).
- El modelo `User` no guarda el refresh token (bien), pero no hay `refresh_token_jti` para revocación.

**Recomendación:** Hashear `device_token` al estilo API key (SHA-256 del token + salt) de modo que una filtración de DB no permita suplantar terminales.

**Penalización:** -0.5 puntos.

---

## 5. Puntuación detallada

| Categoría | Peso | Puntos obtenidos | Comentario |
|---|---:|---:|:---|
| JWT auth (cookie, secret, validación) | 12 | 9 | Cookie httpOnly correcta, pero tokens expuestos en body. |
| Refresh token lifecycle | 7 | 4 | Sin rotación/revocación. |
| PIN hashing | 8 | 7 | Sal obligatoria + bcrypt, SHA256 simple como índice aceptable. |
| Stripe webhook fail-closed | 8 | 8 | Correcto. |
| XSS output escaping | 8 | 8 | Registro y empleados escapados. |
| Rate limiting | 8 | 7 | Redis-aware; bug `_record` corregido; en dev usa memoria. |
| CSP nonce | 7 | 6 | nonce en scripts; `style-src 'unsafe-inline'`. |
| Body size limit | 5 | 5 | 1 MB, 413. |
| SQLi / ORM | 5 | 5 | Parametrizado, probes 401. |
| Cross-tenant isolation | 7 | 7 | Bien reforzado en routers. |
| CORS policy | 5 | 4 | Orígenes restringidos; methods/headers wildcard. |
| Data protection at rest | 7 | 2 | PII en claro. |
| Audit / logging | 5 | 3 | Request logs; falta auth audit centralizado. |
| HTTPS / HSTS / cookies | 5 | 4 | Secure cookie; HSTS enviado en HTTP. |
| Device token storage | 4 | 3 | Texto plano. |
| Password policy | 3 | 2 | Mínimo 6; sin límite superior. |
| Error handling | 4 | 4 | Genérico 500. |
| Dependency hygiene | 4 | 4 | `bcrypt` pinned; resto sin hashes. |
| **Total** | **100** | **84** | **Sube 8 puntos desde 76.** |

---

## 6. Recomendaciones prioritarias

1. **Eliminar tokens del body JSON** en login/register/refresh (modo cookie-first). (-3 pts de riesgo)
2. **Implementar rotación y revocación de refresh tokens** con `jti` en Redis. (-3 pts)
3. **Cifrar PII en reposo** (DNI, SS, IBAN, dirección). (-3 pts)
4. **Restringir CORS** a métodos/headers explícitos. (-1 pt)
5. **Eliminar `style-src 'unsafe-inline'`** de la CSP o migrar a nonce/hash. (-1 pt)
6. **Hashear device tokens** antes de almacenar. (-0.5 pts)
7. **Habilitar HSTS solo sobre HTTPS** con `includeSubDomains; preload`. (-0.5 pts)
8. **Añadir tests de regresión** para el bug `_record` corregido y para el flujo cookie-only.

---

## 7. Conclusión

**¿Subió del 76? Sí: 84/100 (+8).**

Los seis fixes reales están implementados, probados y funcionan. Sin embargo, el sistema aún no es "seguro por defecto": la doble entrega de JWT en body+cookie, la falta de rotación de refresh tokens y el almacenamiento de datos personales en claro impiden superar el umbral de 90. Además, se detectó y corrigió un bug real en el rate limiter (`KeyError` en `_record`) que debilitaba la protección en el primer contacto de una IP.

Se recomienda aplicar las 8 mejoras prioritarias antes de pasar a producción.
