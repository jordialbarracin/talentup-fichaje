# Documento de Seguridad — TalentUP Fichaje

**Versión:** 2.0.0 · **Fecha:** 09 Aug 2026 · **Score de seguridad:** 84/100

> Este documento describe el modelo de amenazas, los controles de seguridad y las prácticas operativas de TalentUP Fichaje, un SaaS multi-tenant de fichaje para hostelería que procesa datos personales de empleados conforme al RGPD, la LOPD-GDD y el RD-ley 8/2019. Cada control se mapea al código real del repositorio.

**Documentos relacionados:**

- [`PRIVACY.md`](./PRIVACY.md) — Política de privacidad (datos personales, derechos ARCO-SUPOL)
- [`DPA.md`](./DPA.md) — Acuerdo de Tratamiento de Datos (Art. 28 RGPD)
- [`SEGURIDAD_FRONTEND.md`](./SEGURIDAD_FRONTEND.md) — Seguridad del frontend (CSP, CORS, XSS, CSRF)
- [`RE_AUDITORIA_SEGURIDAD_FINAL.md`](./RE_AUDITORIA_SEGURIDAD_FINAL.md) — Re-auditoría de seguridad (score 84/100)

---

## Tabla de contenidos

1. [Modelo de amenazas (OWASP Top 10)](#1-modelo-de-amenazas-owasp-top-10)
2. [Autenticación JWT](#2-autenticación-jwt)
3. [Autorización multi-tenant](#3-autorización-multi-tenant)
4. [Protección de datos personales](#4-protección-de-datos-personales)
5. [Cifrado](#5-cifrado)
6. [Seguridad del firmware ESP32](#6-seguridad-del-firmware-esp32)
7. [Seguridad de Stripe](#7-seguridad-de-stripe)
8. [Auditoría y logging](#8-auditoría-y-logging)
9. [Política de contraseñas](#9-política-de-contraseñas)
10. [Gestión de secretos](#10-gestión-de-secretos)
11. [Respuesta a incidentes](#11-respuesta-a-incidentes)

---

## 1. Modelo de amenazas (OWASP Top 10)

TalentUP Fichaje sigue las recomendaciones de OWASP para prevenir las 10 vulnerabilidades web más críticas. A continuación se detalla cada amenaza y su mitigación en el código.

### 1.1 A01:2021 — Broken Access Control

| Control | Implementación | Archivo |
|---------|----------------|---------|
| Aislamiento multi-tenant | RLS en PostgreSQL + filtro `tenant_id` en queries | `backend/alembic/versions/a15b29a48457_enable_rls_tenant_isolation.py` |
| Verificación de pertenencia | Cada endpoint comprueba `current_user.tenant_id == recurso.tenant_id` | `backend/app/routers/billing.py` (línea 126) |
| Roles con permisos granulares | `super_admin`, `owner`, `manager`, `employee` | `backend/app/auth.py` `role_check()` |
| JWT con claim de tenant | El token incluye `tenant_id` y `role` | `backend/app/auth.py` `create_access_token()` |

**Mitigación:** el acceso a recursos se valida en dos capas — aplicación (SQLAlchemy con filtro `tenant_id`) y base de datos (RLS). Si la aplicación olvidara filtrar, la política `tenant_isolation` de PostgreSQL bloquearía la lectura de filas de otros tenants.

### 1.2 A02:2021 — Cryptographic Failures

| Control | Implementación |
|---------|----------------|
| Contraseñas hasheadas | bcrypt (`passlib.context.CryptContext`) |
| JWT firmado | HS256 con `JWT_SECRET` (256 bits, `openssl rand -hex 32`) |
| PIN con sal | SHA-256 first-pass + bcrypt verify; `PIN_HASH_SALT` obligatorio |
| HTTPS/TLS obligatorio | TLS 1.3 en Vercel y Railway; HSTS con preload |
| Cifrado en reposo | AES-256 (PostgreSQL producción) / SQLCipher (SQLite dev) |

### 1.3 A03:2021 — Injection

| Control | Implementación | Evidencia |
|---------|----------------|-----------|
| SQL Injection | SQLAlchemy ORM parametrizado (`select(User).where(User.email == req.email)`) | Pruebas de inyección devuelven 401 sin error de sintaxis |
| Command Injection | No se ejecutan comandos del sistema | Sin `os.system`, `subprocess` con `shell=True` |
| XSS almacenado | `html.escape()` en serialización de modelos + `esc()` en frontend | Payload `<script>` se almacena como `&lt;script&gt;` |

### 1.4 A04:2021 — Insecure Design

| Control | Implementación |
|---------|----------------|
| Validación de input | Pydantic en todos los endpoints (`@field_validator`) |
| Rate limiting por diseño | Login, registro, clock, PIN con límites explícitos |
| Defense in depth | Escape en frontend + backend + CSP como tercera línea |
| Fail-closed | `JWT_SECRET` y `PIN_HASH_SALT` obligatorios en producción (fallan al arrancar) |

### 1.5 A05:2021 — Security Misconfiguration

| Control | Implementación | Archivo |
|---------|----------------|---------|
| CSP estricta | `default-src 'self'`, nonce por petición, sin `unsafe-inline` | `backend/app/main.py` `SecurityHeadersMiddleware` |
| HSTS | `max-age=31536000; includeSubDomains; preload` en producción | `backend/app/main.py` |
| X-Frame-Options | `DENY` (anti-clickjacking) | `backend/app/main.py` |
| X-Content-Type-Options | `nosniff` | `backend/app/main.py` |
| OpenAPI deshabilitado | `/docs`, `/redoc`, `/openapi.json` no disponibles con `APP_ENV=production` | `backend/app/main.py` líneas 114-116 |
| Docker non-root | Usuario `talentup` (UID 1000), sin shell (`/bin/false`) | `backend/Dockerfile` |

### 1.6 A06:2021 — Vulnerable and Outdated Components

| Control | Implementación |
|---------|----------------|
| Dependencias pinneadas | `requirements.txt` con versiones mínimas (`>=`) |
| CI con dos motores de BD | Tests en SQLite y PostgreSQL en GitHub Actions |
| Auditoría periódica | `pip-audit` recomendado; actualizar bcrypt (pin `<4.1.0` por compat) |

### 1.7 A07:2021 — Identification and Authentication Failures

| Control | Implementación |
|---------|----------------|
| Rate limiting de login | 10 intentos fallidos por IP cada 5 min (Redis-backed) |
| Bloqueo de PIN | 5 fallos/min → IP bloqueada 5 min |
| Cookies httpOnly | `access_token` y `refresh_token` no accesibles por JS |
| Refresh token con rotación | Cada uso revoca el anterior (detección de robo) |
| Logout revoca tokens | `POST /api/auth/logout` revoca el refresh token |

### 1.8 A08:2021 — Software and Data Integrity Failures

| Control | Implementación |
|---------|----------------|
| Firmas de webhook | Stripe webhook verifica firma con `STRIPE_WEBHOOK_SECRET` |
| Idempotencia | Stripe maneja idempotency keys nativamente |
| CI/CD firmado | GitHub Actions con `id-token: write` (OIDC) |
| Imágenes Docker | Build multi-stage, sin compiladores en runtime |

### 1.9 A09:2021 — Security Logging and Monitoring Failures

| Control | Implementación |
|---------|----------------|
| Audit log | `backend/app/audit.py` registra acciones críticas |
| Request ID | Cada petición recibe un `X-Request-ID` (UUID) |
| Logging estructurado | JSON con `event`, `method`, `path`, `status_code`, `duration_ms` |
| Métricas Prometheus | `/api/metrics/prometheus` para scraping |
| Health check profundo | `/api/health` verifica DB + Redis + uptime |

### 1.10 A10:2021 — Server-Side Request Forgery (SSRF)

| Control | Implementación |
|---------|----------------|
| Sin fetch de URLs arbitrarias | El backend no acepta URLs del usuario para fetch |
| `connect-src 'self'` | CSP bloquea conexiones a dominios externos |
| CORS lista blanca | Sólo `talentup.es` y `www.talentup.es` en producción |

---

## 2. Autenticación JWT

### 2.1 Arquitectura del JWT

TalentUP usa JWT (JSON Web Tokens) con dos tipos de token:

| Token | Algoritmo | Expiración | Almacenamiento |
|-------|-----------|------------|----------------|
| Access token | HS256 | 8 horas (`JWT_EXPIRE_MINUTES=480`) | Cookie httpOnly `access_token` |
| Refresh token | HS256 | 30 días (`JWT_REFRESH_EXPIRE_DAYS=30`) | Cookie httpOnly `refresh_token` |

**Decisión arquitectónica:** el JWT **nunca** se persiste en `localStorage` ni `sessionStorage`. Se gestiona exclusivamente mediante cookies httpOnly, de modo que JavaScript no puede leer el token y un ataque XSS no puede robarlo.

### 2.2 Claims del token

```python
# backend/app/auth.py — create_access_token()
{
    "sub": "<user_id>",        # Subject (user ID)
    "email": "owner@rest.es",  # Email del usuario
    "role": "owner",           # Rol: super_admin | owner | manager | employee
    "tenant_id": "<uuid>",     # Tenant al que pertenece
    "exp": 1234567890,         # Expiración (timestamp)
    "type": "access"           # Tipo: access | refresh
}
```

### 2.3 Cookies httpOnly

```python
# backend/app/routers/auth.py — login()
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,              # JS no puede leer la cookie
    secure=_COOKIE_SECURE,     # True en producción (HTTPS only)
    samesite=_COOKIE_SAMESITE, # "lax" en producción (anti-CSRF)
    max_age=28800,              # 8 horas
)
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=_COOKIE_SECURE,
    samesite=_COOKIE_SAMESITE,
    max_age=REFRESH_TOKEN_TTL_SECONDS,  # 30 días
)
```

| Atributo | Valor (prod) | Motivo |
|----------|--------------|--------|
| `httponly` | `True` | JS no puede leer la cookie → inmunidad a robo por XSS |
| `secure` | `True` | Sólo se envía sobre HTTPS |
| `samesite` | `Lax` | Protección CSRF (no se envía en POST cross-site) |
| `max_age` access | 28800s (8h) | Vida corta; rotación frecuente |
| `max_age` refresh | 30 días | Rotación: cada uso revoca el anterior |

### 2.4 Rotación de secretos

- **Generación:** `JWT_SECRET` se genera con `openssl rand -hex 32` (256 bits).
- **Obligación:** `JWT_SECRET` es **obligatorio en producción**. Si falta, el backend falla al arrancar con `RuntimeError: JWT_SECRET requerido en produccion`.
- **Rotación:** al rotar `JWT_SECRET`, todos los tokens emitidos con el secreto anterior quedan invalidados. Los usuarios deben volver a hacer login. Esto es esperado y se debe comunicar.
- **Frecuencia recomendada:** rotación cada 90 días. Documentar el cambio en el audit log.

### 2.5 Expiración de tokens

| Token | Expiración | Variable |
|-------|------------|----------|
| Access token | 8 horas (480 min) | `JWT_EXPIRE_MINUTES` |
| Refresh token | 30 días | `JWT_REFRESH_EXPIRE_DAYS` |

**Renovación:** el frontend llama a `POST /api/auth/refresh` cuando el access token expira. El backend lee el refresh token de la cookie httpOnly, valida que no esté revocado, emite un nuevo access token y **revoca el refresh token anterior** (rotación).

### 2.6 Refresh tokens con rotación

```python
# backend/app/routers/auth.py — refresh()
# 1. Leer refresh token SOLO de la cookie httpOnly
refresh_token = request.cookies.get("refresh_token")

# 2. Validar que no esté revocado
if await _is_refresh_token_revoked(refresh_token):
    raise HTTPException(401, "Refresh token revocado")

# 3. Rotar: revocar el token usado
await _revoke_refresh_token(refresh_token)

# 4. Emitir nuevo access token + nuevo refresh token
new_refresh_token = create_refresh_token(user)
```

**Revocación en Redis:** los refresh tokens revocados se guardan en Redis con TTL de 30 días (`refresh:revoked:<key>`). Si un atacante roba un refresh token y lo usa, el legítimo usuario detectará que su token fue revocado (detección de robo).

**Protección contra reuso:** si un refresh token revocado se presenta de nuevo, el backend devuelve `401 Refresh token revocado`.

---

## 3. Autorización multi-tenant

### 3.1 Modelo de aislamiento

TalentUP es multi-tenant: cada empresa (tenant) solo puede ver y modificar sus propios datos. El aislamiento se aplica en **dos capas**:

1. **Capa de aplicación:** todas las queries SQLAlchemy filtran por `tenant_id` (extraído del JWT).
2. **Capa de base de datos:** Row Level Security (RLS) en PostgreSQL como red de seguridad.

### 3.2 RLS en PostgreSQL

La migración `a15b29a48457` habilita RLS en 13 tablas de negocio:

```sql
-- Tablas con RLS:
-- employees, clock_ins, shifts, schedules, vacation_requests,
-- leaves, holidays, overtime, payroll, notifications,
-- contracts, incidents, devices, billing_records

ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON {table}
USING (tenant_id = current_setting('app.tenant_id')::text);
```

La política compara el `tenant_id` de cada fila con la variable de sesión `app.tenant_id`, que la aplicación debe establecer antes de emitir queries:

```python
# La aplicación setea la variable de sesión antes de cada query:
SET app.tenant_id = '<tenant_uuid>';
SELECT * FROM employees;  -- Sólo devuelve filas del tenant indicado
```

**Verificación de RLS:**

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND rowsecurity = true;
-- Debe devolver las 13 tablas con rowsecurity = true
```

### 3.3 Verificación de pertenencia en endpoints

Cada endpoint que accede a un recurso verifica que el usuario pertenece al tenant del recurso:

```python
# backend/app/routers/billing.py — create_checkout_session()
if str(current_user.tenant_id) != str(data.tenant_id):
    raise HTTPException(status_code=403, detail="No tienes acceso a este tenant")
```

```python
# backend/app/routers/billing.py — get_billing_status()
if str(current_user.tenant_id) != str(tenant_id):
    raise HTTPException(status_code=403, detail="No tienes acceso a este tenant")
```

### 3.4 Roles y permisos

| Rol | Permisos | Dependency |
|-----|---------|------------|
| `super_admin` | Acceso a todos los tenants, configuración global | `require_super_admin` |
| `owner` | Gestión completa de su tenant (usuarios, billing, config) | `require_owner` |
| `manager` | Gestión de empleados, turnos, fichajes | `require_manager` |
| `employee` | Solo fichar y ver sus propios fichajes | (default) |

```python
# backend/app/auth.py
def role_check(*allowed_roles: str):
    async def _role_check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Se requiere rol: {', '.join(allowed_roles)}")
        return current_user
    return _role_check

require_super_admin = role_check("super_admin")
require_owner = role_check("super_admin", "owner")
require_manager = role_check("super_admin", "owner", "manager")
```

### 3.5 Prevención de IDOR (Insecure Direct Object Reference)

El `tenant_id` se extrae **siempre** del JWT (claim `tenant_id`), nunca de un parámetro de la petición. Esto previene IDOR: un usuario no puede acceder a recursos de otro tenant manipulando IDs en la URL.

---

## 4. Protección de datos personales

### 4.1 Marco normativo

TalentUP Fichaje procesa datos personales de empleados y está sujeto a:

| Normativa | Ámbito | Requisito clave |
|-----------|--------|-----------------|
| **RGPD** (Reglamento UE 2016/679) | Europeo | Consentimiento, minimización, seguridad, derechos ARCO-SUPOL |
| **LOPD-GDD** (Ley 3/2018) | España | Adaptación nacional del RGPD; encargados del tratamiento |
| **RD-ley 8/2019** | España | Registro obligatorio de jornada laboral (art. 1) |
| **Estatuto de los Trabajadores** | España | Conservación de registros (4 años, art. 66) |

### 4.2 Categorías de datos tratados

| Categoría | Datos concretos | Base legal |
|-----------|-----------------|-----------|
| Datos identificativos | Nombre, apellidos, DNI/NIE, email, teléfono | Art. 6.1.b RGPD (contrato) |
| Datos de fichaje | Fecha, hora entrada/salida, pausas, incidencias | Art. 6.1.c RGPD (obligación legal: RD-ley 8/2019) |
| Datos laborales | Puesto, turno, centro, horario asignado | Art. 6.1.b RGPD (contrato) |
| Datos de cuenta | Usuario, hash de contraseña, rol, tenant | Art. 6.1.f RGPD (interés legítimo) |

**No se tratan** datos especialmente protegidos (salud, ideología, religión, etc.) ni datos de menores de edad.

### 4.3 Principios aplicados

- **Minimización:** sólo se recogen los datos necesarios para el registro de jornada.
- **Finalidad:** los datos se usan exclusivamente para control horario, nómina y seguridad del sistema.
- **Conservación:** 4 años desde el registro (RD-ley 8/2019, art. 21; Estatuto de los Trabajadores, art. 66). Transcurrido, se suprimen de forma segura.
- **Transferencias:** los datos se almacenan en servidores de la UE (Supabase AWS Frankfurt, Vercel edge EU). No hay transferencias fuera del EEE.

### 4.4 Derechos ARCO-SUPOL

Los empleados pueden ejercer sus derechos dirigiéndose a `privacidad@talentup.app`:

| Derecho | Descripción | Plazo de respuesta |
|--------|-------------|-------------------|
| Acceso | Saber qué datos se tienen y para qué | 30 días |
| Rectificación | Corregir datos inexactos | 30 días |
| Supresión | Eliminar datos (salvo obligación legal) | 30 días |
| Oposición | Oponerse al tratamiento para fines específicos | 30 días |
| Limitación | Restringir el tratamiento | 30 días |
| Portabilidad | Recibir datos en formato estructurado (JSON/CSV) | 30 días |

### 4.5 Encargados del tratamiento (subencargados)

| Subencargado | Servicio | Ubicación | DPA |
|--------------|----------|-----------|-----|
| Supabase / PostgreSQL | Base de datos | EU (Frankfurt) | Sí |
| Vercel | Hosting frontend/edge | EU | Sí |
| Cloudflare | CDN/DNS | Global (nodos EU) | Sí |
| Railway | Hosting backend | EU | Sí |

El DPA (`DPA.md`) regula la relación con el responsable del tratamiento conforme al Art. 28 RGPD.

### 4.6 Notificación de violaciones (Data Breach)

Conforme al Art. 33 RGPD:

1. **Detección:** detección automática (alertas de monitoring) o notificación manual.
2. **Notificación al responsable:** en menos de 24 horas.
3. **Notificación a la AEPD:** en 72 horas si existe riesgo para los interesados.
4. **Notificación a los afectados:** sin demora indebida si existe alto riesgo.
5. **Documentación:** registro de naturaleza, alcance, medidas tomadas.

---

## 5. Cifrado

### 5.1 Cifrado en tránsito (HTTPS/TLS)

| Capa | Protocolo | Configuración |
|------|-----------|---------------|
| Frontend (Vercel) | TLS 1.3 (preferido), TLS 1.2 (fallback) | Let's Encrypt, renovación automática |
| Backend (Railway) | TLS 1.3 en `*.railway.app` | Certificado automático de Railway |
| Backend → DB | TLS en connection string | `sslmode=require` en `DATABASE_URL` |
| Backend → Redis | TLS si Redis lo soporta | Configurado por Railway add-on |
| ESP32 → Backend | HTTPS (recomendado en prod) | `WiFiClientSecure` disponible |

**HSTS (HTTP Strict Transport Security):**

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

Se emite cuando `APP_ENV=production` o el proxy indica HTTPS (`X-Forwarded-Proto: https`).

### 5.2 Cifrado en reposo

| Recurso | Cifrado | Notas |
|---------|---------|-------|
| PostgreSQL (producción) | AES-256 | Cifrado a nivel de servicio del proveedor |
| SQLite (desarrollo) | SQLCipher | Cifrado opcional para dev local |
| Backups | Cifrados | Backups del proveedor con cifrado en reposo |
| Redis | Cifrado en reposo | Configurado por Railway |

### 5.3 Hash de contraseñas y PIN

| Dato | Algoritmo | Implementación |
|------|-----------|----------------|
| Contraseña de usuario | bcrypt | `passlib.context.CryptContext(schemes=["bcrypt"])` |
| PIN de empleado | SHA-256 first-pass + bcrypt verify | `compute_pin_hash_fast()` + `verify_password()` |

**PIN de empleado (doble capa):**

1. **SHA-256 + sal:** hash rápido para lookup indexado (`PIN_HASH_SALT` obligatorio).
2. **bcrypt verify:** verificación autoritativa con hash bcrypt almacenado.

```python
# backend/app/auth.py
def compute_pin_hash_fast(pin: str) -> str:
    """Hash rápido para lookup por índice. NO reemplaza bcrypt."""
    return hashlib.sha256((pin + _SECRET_SALT).encode("utf-8")).hexdigest()
```

> `PIN_HASH_SALT` es **obligatorio en todos los entornos**. Si falta, el backend falla al arrancar con `RuntimeError: PIN_HASH_SALT requerido`.

### 5.4 Backups cifrados

- **Frecuencia:** diario.
- **Retención:** 30 días.
- **Cifrado:** los backups del proveedor de BD van cifrados en reposo.
- **Restauración:** probar la restauración de backup al menos una vez al trimestre.

---

## 6. Seguridad del firmware ESP32

El dispositivo físico de fichaje es un **ESP32 CYD 2432S028** con lector NFC PN532 conectado por I2C. El firmware vive en `hardware/esp32_fichaje_cyd/src/esp32_fichaje_cyd.ino`.

### 6.1 Modelo de amenazas del dispositivo

| Amenaza | Impacto | Probabilidad |
|---------|---------|---------------|
| Falsificación de tarjeta NFC | Fichaje fraudulento | Media |
| Acceso físico al dispositivo | Extracción de credenciales WiFi | Media |
| Intercepción de tráfico HTTP | Robo de UID de empleados | Baja (si HTTPS) |
| OTA no autorizado | Firmware malicioso | Media |
| Ataque de fuerza bruta al backend vía NFC | Spam de fichajes | Baja (rate limited) |

### 6.2 OTA (Over-the-Air updates)

```cpp
// hardware/esp32_fichaje_cyd/src/esp32_fichaje_cyd.ino
void initOTA() {
    ArduinoOTA.setHostname("talentup-fichaje-cyd");
    ArduinoOTA.setPassword("talentup2024");
    // ... callbacks onStart, onProgress, onEnd, onError
    ArduinoOTA.begin();
}
```

**Estado actual y recomendaciones:**

| Control | Estado | Recomendación |
|---------|--------|---------------|
| Contraseña OTA | Hardcodeada (`talentup2024`) | **CRÍTICO:** usar contraseña fuerte única, cargarla por build_flag o NVS |
| OTA firmado | No implementado | **ALTO:** implementar firma de firmware (ESP-IDF secure boot) |
| OTA sobre HTTPS | No (ArduinoOTA usa mDNS + TCP) | **MEDIO:** usar HTTPS para transferencia de firmware |
| Autenticación mutua | No | **MEDIO:** certificado de cliente para OTA |

### 6.3 Credenciales WiFi

```ini
# hardware/esp32_fichaje_cyd/platformio.ini
build_flags =
    -DWIFI_SSID=\"JordiAlba\"
    -DWIFI_PASS=\"qwertyuio\"
    -DBACKEND_URL=\"http://192.168.0.16:8000\"
    -DTENANT_ID=\"default\"
```

**Problemas de seguridad actuales:**

1. **Credenciales en texto plano en `platformio.ini`:** el SSID y password WiFi están hardcodeados en el archivo de configuración del build. Si este archivo se sube al repositorio (lo está), las credenciales son visibles para cualquiera con acceso al repo.
2. **`BACKEND_URL` en HTTP:** el dispositivo envía fichajes por HTTP plano (sin TLS). En producción debe usar HTTPS.

**Recomendaciones de provisioning seguro:**

| Práctica | Descripción |
|----------|--------------|
| **Provisioning por WiFi captive portal** | El dispositivo arranca en modo AP; el instalador se conecta y introduce credenciales por web. No se almacenan en el firmware. |
| **NVS (Non-Volatile Storage) cifrado** | Usar `nvs_flash` con cifrado de particiones para guardar SSID/password fuera del firmware. |
| **`BACKEND_URL` por build_flag** | Compilar cada dispositivo con su `TENANT_ID` y `BACKEND_URL` por build_flag, no hardcodear en `.ino`. |
| **`platformio.ini` en `.gitignore`** | Excluir `platformio.ini` del repositorio o usar un template `platformio.ini.example`. |
| **HTTPS obligatorio** | Usar `WiFiClientSecure` en lugar de `WiFiClient` para las llamadas al backend. |
| **Certificado CA** | Almacenar el certificado CA del backend en flash y verificar en cada conexión. |

### 6.4 Cola offline (SPIFFS)

Cuando no hay WiFi, el dispositivo encola fichajes en SPIFFS:

```cpp
#define QUEUE_FILE        "/fichajes_queue.json"
#define QUEUE_MAX_ENTRIES 50
```

- **Datos encolados:** `nfc_uid`, `tenant_id`, `timestamp` (Unix epoch).
- **Límite:** 50 entradas máximo (evita agotar SPIFFS).
- **Flush:** cada 15s si hay WiFi, envía los pendientes al backend.
- **Riesgo:** si el dispositivo es robado, los UIDs encolados están en texto plano en SPIFFS. **Recomendación:** cifrar la partición SPIFFS o usar `LittleFS` con cifrado.

### 6.5 Anti-lectura duplicada (debounce)

```cpp
#define DEBOUNCE_MS 3000    // Evita doble lectura de la misma tarjeta

void processNFCTag() {
    // ...
    if (now - lastReadTime < DEBOUNCE_MS) return;
    lastReadTime = now;
    if (uidStr == lastUID) return;  // Misma tarjeta consecutiva
    // ...
}
```

### 6.6 Watchdog

```cpp
#define WDT_TIMEOUT_S 30
void initWatchdog() {
    esp_task_wdt_init(WDT_TIMEOUT_S, true);  // panic on timeout
    esp_task_wdt_add(NULL);
}
void feedWdt() { esp_task_wdt_reset(); }
```

El watchdog reinicia el dispositivo si el bucle principal se cuelga más de 30s (anti-bloqueo).

### 6.7 Rate limiting en el backend para NFC

El backend aplica rate limiting a los fichajes NFC:

- **10 fichajes/min** por `(IP, tenant_id)`.
- **100 fichajes/hora** por `tenant_id`.
- **5 fallos de PIN/min** → IP bloqueada 5 minutos (`PIN_BLOCK_MINUTES=5`).

Esto mitiga el spam de fichajes desde un dispositivo comprometido.

---

## 7. Seguridad de Stripe

### 7.1 Verificación de webhook (firma)

El endpoint `/api/billing/webhook` verifica la firma de Stripe de forma **fail-closed**:

```python
# backend/app/routers/billing.py
if not STRIPE_WEBHOOK_SECRET:
    raise HTTPException(status_code=403, detail="Webhook secret no configurado")

sig_header = request.headers.get("stripe-signature", "")
if not sig_header:
    raise HTTPException(status_code=400, detail="Firma de webhook requerida")

payload = await request.body()

try:
    event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid payload")
except stripe.error.SignatureVerificationError:
    raise HTTPException(status_code=400, detail="Invalid signature")
```

| Estado | HTTP | Causa |
|--------|------|-------|
| Sin secret configurado | 403 | Fail-closed: no procesar sin verificar |
| Sin cabecera de firma | 400 | Petición inválida |
| Payload inválido | 400 | JSON corrupto |
| Firma inválida | 400 | Webhook no viene de Stripe |
| Firma válida | 200 | Evento procesado |

### 7.2 Eventos suscritos

| Evento | Handler | Acción |
|--------|--------|--------|
| `checkout.session.completed` | `_handle_checkout_completed` | Activa plan, crea `BillingRecord` |
| `invoice.paid` | `_handle_invoice_paid` | Registra pago, actualiza `current_period_end` |
| `customer.subscription.deleted` | `_handle_subscription_deleted` | Marca tenant como `canceled` |
| `customer.subscription.updated` | `_handle_subscription_updated` | Sincroniza estado de suscripción |

### 7.3 Idempotency keys

Stripe gestiona idempotency keys nativamente. El backend crea checkout sessions con metadata de `tenant_id` y `plan`:

```python
session = stripe.checkout.Session.create(
    customer=customer_id,
    mode=mode,
    line_items=[{"price": price_id, "quantity": 1}],
    metadata={"tenant_id": str(tenant.id), "plan": data.plan},
    # ...
)
```

**Recomendación:** para operaciones de backend que no sean idempotentes (como crear customer), usar `idempotency_key` explícito:

```python
stripe.Customer.create(
    email=...,
    name=...,
    idempotency_key=f"tenant_{tenant_id}_customer",  # Evita duplicados
)
```

### 7.4 Verificación de pertenencia

Antes de crear una checkout session, el backend verifica que el usuario pertenece al tenant:

```python
if str(current_user.tenant_id) != str(data.tenant_id):
    raise HTTPException(status_code=403, detail="No tienes acceso a este tenant")
```

Esto previene que un usuario cree una sesión de pago para un tenant ajeno.

### 7.5 Configuración segura de claves

| Clave | Variable | Almacenamiento |
|-------|----------|----------------|
| Secret key (live) | `STRIPE_SECRET_KEY` | Railway secrets (nunca en git) |
| Webhook secret | `STRIPE_WEBHOOK_SECRET` | Railway secrets |
| Price IDs | `STRIPE_PRICE_*` | Railway variables (no sensibles) |

- **Nunca** usar la secret key en el frontend.
- **Nunca** subir `.env` al repositorio (el `.gitignore` lo excluye).
- Rotar la secret key si se sospecha compromiso (Stripe Dashboard → Developers → API keys).

### 7.6 Logging de eventos de Stripe

```python
logger.info(f"Stripe webhook received: {event_type}")
logger.info(f"Tenant {tenant_id} updated to plan {plan} (active)")
logger.warning(f"checkout.session.completed missing tenant_id in metadata")
```

Todos los eventos de Stripe se loguean con el `tenant_id` para trazabilidad.

---

## 8. Auditoría y logging

### 8.1 Audit log

El backend mantiene un audit log de acciones críticas:

```python
# backend/app/audit.py
async def log_action(
    db: AsyncSession,
    tenant_id: Any,
    user_id: Any,
    action: str,
    entity_type: str,
    entity_id: Any = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
) -> AuditLog:
    log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    return log
```

**Eventos auditados:**

| Acción | Entity type | Registro |
|--------|-------------|----------|
| Crear empleado | `employee` | Creado por, datos nuevos |
| Modificar empleado | `employee` | Datos antiguos y nuevos |
| Eliminar empleado | `employee` | Datos eliminados |
| Crear fichaje | `clock_in` | Empleado, timestamp, tipo |
| Crear incidencia | `incident` | Descripción, tipo |
| Cambio de plan | `tenant` | Plan anterior y nuevo |
| Login / logout | `user` | IP, timestamp |

### 8.2 Request logging

Cada petición HTTP se loguea con contexto:

```json
{
  "event": "request",
  "method": "POST",
  "path": "/api/auth/login",
  "status_code": 200,
  "duration_ms": 45.2,
  "request_id": "a1b2c3d4-e5f6-..."
}
```

- **Request ID:** UUID por petición, propagado a logs y cabecera `X-Request-ID`.
- **Filtro:** health checks y métricas no se loguean en INFO (reducir ruido).
- **Errores 500:** se loguean con stack trace completo (`logger.exception`).

### 8.3 Logging estructurado (JSON)

En producción (`LOG_FORMAT=json`), los logs son JSON parseable:

```bash
# Railway logs en JSON
railway logs --filter "ERROR"
# {"event":"request_error","method":"POST","path":"/api/clock/nfc",
#  "duration_ms":5000,"request_id":"...","error":"timeout"}
```

### 8.4 Métricas de seguridad

El endpoint `/api/metrics` expone:

```json
{
  "uptime_seconds": 3600,
  "requests_today": 15423,
  "errors_today": 3,
  "active_tenants": 12,
  "total_employees": 342
}
```

Prometheus expone además:

- `http_requests_total{method,endpoint,status}` — para detectar picos de errores.
- `http_request_duration_seconds{method,endpoint}` — para detectar degradación.

### 8.5 Retención de logs

| Tipo | Retención | Notas |
|------|-----------|-------|
| Logs de aplicación | 30 días | Railway retiene logs por defecto |
| Audit log (DB) | 4 años | Conforme a RD-ley 8/2019 |
| Métricas Prometheus | 15 días | Configurable en Prometheus |

### 8.6 Alertas recomendadas

| Alerta | Condición | Severidad |
|--------|-----------|-----------|
| Health check caído | `/api/health` ≠ 200 durante 2 min | Crítica |
| Errores 5xx masivos | >10 errores 5xx/min | Alta |
| Latencia alta | P95 > 2s durante 5 min | Media |
| Rate limiting activo | >100 respuestas 429/min | Media |
| DB desconectada | `db_status: error` | Crítica |
| Redis desconectado | `redis_status: error` | Alta |

---

## 9. Política de contraseñas

### 9.1 Requisitos mínimos

| Requisito | Valor | Implementación |
|-----------|-------|----------------|
| Longitud mínima | 6 caracteres | `@field_validator("password")` en `RegisterRequest` |
| Hash | bcrypt | `passlib.context.CryptContext` |
| No en texto plano | Siempre hasheada | `hash_password()` en registro |
| Verificación | bcrypt `verify` | `verify_password()` en login |

```python
# backend/app/routers/auth.py
class RegisterRequest(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v
```

### 9.2 Recomendaciones (a implementar)

| Recomendación | Estado | Prioridad |
|---------------|--------|-----------|
| Longitud mínima 8 caracteres | No implementado | Alta |
| Complejidad (mayús, minús, número) | No implementado | Media |
| No reutilización (histórico) | No implementado | Media |
| Bloqueo tras N intentos | Implementado (10/5min) | ✅ |
| Reset por email | No implementado | Alta |
| 2FA / MFA | No implementado | Alta (para owner/admin) |
| Detección de contraseñas comprometidas (HaveIBeenPwned) | No implementado | Media |

### 9.3 PIN de empleado

Los empleados pueden fichar con un PIN numérico (alternativa a NFC):

| Requisito | Valor |
|-----------|-------|
| Longitud | 4-6 dígitos |
| Hash | SHA-256 first-pass (indexado) + bcrypt verify |
| Sal | `PIN_HASH_SALT` (obligatorio, 32 hex) |
| Intentos | 5 fallos/min → bloqueo 5 min |
| Rate limit | 10 fichajes/min por (IP, tenant_id) |

### 9.4 Almacenamiento seguro

- **Contraseñas:** bcrypt (hash con sal automática, cost factor por defecto de passlib).
- **PINs:** bcrypt (hash) + SHA-256 indexado (para lookup rápido sin iterar).
- **Nunca** se almacenan contraseñas ni PINs en texto plano.
- **Nunca** se loguean contraseñas ni PINs en logs.

---

## 10. Gestión de secretos

### 10.1 Principios

1. **Nunca en git:** los secretos NO se suben al repositorio. El `.gitignore` excluye `.env`.
2. **Secrets en el proveedor:** Railway Variables, Vercel Environment Variables.
3. **Rotación:** rotar secretos críticos cada 90 días.
4. **Mínimo privilegio:** cada componente solo tiene acceso a los secretos que necesita.
5. **Auditoría:** registrar quién accede y cuándo se rotan los secretos.

### 10.2 Archivo `.env.example`

El repositorio incluye `.env.example` como template. **No contiene secretos reales**, solo placeholders:

```bash
# .env.example (versiones de ejemplo)
JWT_SECRET=generar-uno-seguro
PIN_HASH_SALT=generar-uno-seguro
STRIPE_SECRET_KEY=sk_test_...o_omitir_en_local
STRIPE_WEBHOOK_SECRET=whsec_...o_omitir_en_local
```

### 10.3 Generación de secretos

```bash
# JWT_SECRET (256 bits, 64 hex chars)
openssl rand -hex 32

# PIN_HASH_SALT (128 bits, 32 hex chars)
openssl rand -hex 16

# Contraseña de base de datos
openssl rand -base64 24

# Secreto de webhook de Stripe
# → Generado por Stripe Dashboard (no manual)
```

### 10.4 Almacenamiento por entorno

| Secreto | Desarrollo | Staging | Producción |
|---------|------------|---------|------------|
| `JWT_SECRET` | Generado aleatorio (warning) | Railway variable | Railway variable (rotado) |
| `PIN_HASH_SALT` | `.env` local | Railway variable | Railway variable |
| `DATABASE_URL` | SQLite local | Railway PostgreSQL | Railway PostgreSQL |
| `REDIS_URL` | None (in-memory) | Railway Redis | Railway Redis |
| `STRIPE_SECRET_KEY` | `sk_test_...` | `sk_test_...` | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` (test) | Railway variable | Railway variable |
| `CORS_ORIGINS` | `localhost:3000` | `staging.talentup.es` | `talentup.es` |

### 10.5 Verificación de que no hay secretos en git

```bash
# Buscar secretos en el historial de git
git log --all -p | grep -E "(sk_live_|whsec_|JWT_SECRET=|PIN_HASH_SALT=)" | head

# Si encuentras secretos comprometidos:
# 1. Rotarlos inmediatamente (Stripe, JWT, PIN)
# 2. Eliminarlos del historial con git-filter-repo o BFG
# 3. Force push (con coordinación del equipo)
```

### 10.6 Secretos en el firmware ESP32

**Problema actual:** `platformio.ini` contiene credenciales WiFi y URL del backend en texto plano:

```ini
build_flags =
    -DWIFI_SSID=\"JordiAlba\"
    -DWIFI_PASS=\"qwertyuio\"
    -DBACKEND_URL=\"http://192.168.0.16:8000\"
```

**Recomendaciones:**

1. **Mover `platformio.ini` a `.gitignore`** y crear `platformio.ini.example` como template.
2. **Provisioning por captive portal:** el dispositivo arranca en modo AP, el instalador introduce credenciales por web (se guardan en NVS cifrado).
3. **HTTPS obligatorio:** usar `WiFiClientSecure` con certificado CA del backend.

### 10.7 Gestor de secretos recomendado

Para el equipo de desarrollo, usar un gestor de secretos (no archivos de texto):

| Herramienta | Uso |
|-------------|-----|
| **1Password / Bitwarden** | Almacenar secretos de producción compartidos |
| **Railway Variables** | Secretos del backend (encriptados en reposo) |
| **Vercel Environment Variables** | Variables del frontend |
| **GitHub Secrets** | Tokens de CI/CD (`RAILWAY_TOKEN`, `GITHUB_TOKEN`) |

---

## 11. Respuesta a incidentes

### 11.1 Plan de respuesta

| Fase | Acción | Tiempo objetivo |
|------|--------|-----------------|
| **1. Detección** | Alerta de monitoring, reporte manual, audit log anómalo | — |
| **2. Triage** | Clasificar severidad (crítica/alta/media/baja), asignar responsable | < 30 min |
| **3. Contención** | Aislar el sistema afectado (rollback, bloqueo de IP, revocar tokens) | < 1h |
| **4. Erradicación** | Eliminar la causa raíz (parchear, rotar secretos, limpiar) | < 4h |
| **5. Recuperación** | Restaurar servicio, verificar integridad | < 8h |
| **6. Notificación** | Afectados, AEPD (72h si breach de datos), responsable del tratamiento | < 72h |
| **7. Postmortem** | Documentar causa, impacto, acciones preventivas | < 1 semana |

### 11.2 Clasificación de severidad

| Severidad | Ejemplo | Respuesta |
|-----------|---------|-----------|
| **Crítica** | Breach de datos de empleados, acceso no autorizado a todos los tenants | Contención inmediata, notificación AEPD |
| **Alta** | Compromiso de `JWT_SECRET`, webhook de Stripe sin firma, RLS deshabilitado | Rotar secretos, rollback, auditoría |
| **Media** | Rate limit insuficiente, credenciales OTA débiles, `platformio.ini` en git | Parchear en próxima release |
| **Baja** | `style-src 'unsafe-inline'` en CSP, OpenAPI expuesto | Mejora de hardening |

### 11.3 Contactos de emergencia

- **DPO / Protección de datos:** `privacidad@talentup.app`
- **AEPD (reclamaciones):** https://www.aepd.es
- **Stripe (fraude de pagos):** Stripe Dashboard → dispute management

### 11.4 Herramientas de respuesta

| Herramienta | Uso |
|-------------|-----|
| `railway rollback` | Rollback del backend a versión anterior |
| `railway logs` | Revisión de logs de incidente |
| `vercel promote <url>` | Rollback del frontend |
| `alembic downgrade` | Rollback de migraciones de BD (con backup previo) |
| Railway Variables | Rotación de secretos sin redeploy |
| Audit log (DB) | Investigación de acciones de usuario |

---

**Score de seguridad global: 84/100** (auditoría interna, ver `RE_AUDITORIA_SEGURIDAD_FINAL.md`).

**Riesgos residuales conocidos:**

| Riesgo | Severidad | Mitigación planificada |
|--------|-----------|------------------------|
| Credenciales WiFi en `platformio.ini` (en git) | Alta | Mover a `.gitignore` + provisioning por captive portal |
| OTA sin firma criptográfica | Alta | Implementar ESP-IDF secure boot |
| `BACKEND_URL` en HTTP (no HTTPS) en ESP32 | Alta | Usar `WiFiClientSecure` con certificado CA |
| Contraseña OTA hardcodeada (`talentup2024`) | Alta | Cargar por build_flag o NVS, contraseña fuerte |
| `style-src 'unsafe-inline'` residual en CSP | Baja | Necesario para frontend vanilla; refactor a nonce |
| Sin 2FA para owner/admin | Media | Implementar TOTP o WebAuthn |
| Sin reset de contraseña por email | Media | Implementar flujo de reset con token temporal |
| Longitud mínima de contraseña 6 | Media | Subir a 8 + complejidad |

**Revisión del documento:** este documento debe revisarse trimestralmente y tras cada auditoría de seguridad o incidente.