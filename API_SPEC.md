# TalentUP Fichaje — Especificación de API REST

**Versión API:** 1.0  
**Base URL (producción):** `https://talentup-fichaje.up.railway.app`  
**Base URL (desarrollo):** `http://localhost:8000`  
**Prefijo de versión:** `/api/v1/` *(planificado — actualmente los routers usan `/api/`)*  
**Formato:** JSON  
**Codificación:** UTF-8  
**Auth:** JWT Bearer (HS256) + httpOnly cookies  
**Routers:** 19 routers FastAPI

> **Nota de versionado:** Los routers actuales usan el prefijo `/api/` (ej: `/api/employees`). El roadmap v1.0 contempla migrar a `/api/v1/` para versionado explícito. Esta especificación documenta los endpoints tal como existen actualmente con prefijo `/api/`.

---

## Tabla de contenidos

1. [Convenciones generales](#1-convenciones-generales)
2. [Autenticación](#2-autenticación)
3. [Rate limiting](#3-rate-limiting)
4. [Paginación](#4-paginación)
5. [Modelos de respuesta](#5-modelos-de-respuesta)
6. [Dominio: Auth](#6-dominio-auth)
7. [Dominio: Tenants](#7-dominio-tenants)
8. [Dominio: Employees](#8-dominio-employees)
9. [Dominio: Shifts](#9-dominio-shifts)
10. [Dominio: Schedules](#10-dominio-schedules)
11. [Dominio: Clock Events (Fichajes)](#11-dominio-clock-events-fichajes)
12. [Dominio: Incidents](#12-dominio-incidents)
13. [Dominio: Contracts](#13-dominio-contracts)
14. [Dominio: Holidays](#14-dominio-holidays)
15. [Dominio: Vacations](#15-dominio-vacations)
16. [Dominio: Leave (Bajas IT)](#16-dominio-leave-bajas-it)
17. [Dominio: Overtime (Horas Extra)](#17-dominio-overtime-horas-extra)
18. [Dominio: Payroll (Nóminas)](#18-dominio-payroll-nóminas)
19. [Dominio: Notifications](#19-dominio-notifications)
20. [Dominio: Calendar (Calendario Laboral)](#20-dominio-calendar-calendario-laboral)
21. [Dominio: Settings](#21-dominio-settings)
22. [Dominio: Billing (Stripe)](#22-dominio-billing-stripe)
23. [Dominio: Devices (Terminales)](#23-dominio-devices-terminales)
24. [Dominio: Reports (Informes)](#24-dominio-reports-informes)
25. [Endpoints de sistema](#25-endpoints-de-sistema)
26. [Resumen de códigos de estado](#26-resumen-de-códigos-de-estado)

---

## 1. Convenciones generales

### 1.1 Formato de fechas

- **Fechas:** ISO 8601 `YYYY-MM-DD` (ej: `2026-08-09`)
- **Timestamps:** ISO 8601 con timezone `2026-08-09T14:30:00+00:00`
- **Horas (turnos):** `HH:MM` 24h (ej: `08:00`, `16:30`)

### 1.2 IDs

Todos los IDs son **UUID v4** como strings de 36 caracteres:
```
"550e8400-e29b-41d4-a716-446655440000"
```

### 1.3 Content-Type

```
Content-Type: application/json
```

### 1.4 Charset

UTF-8 en todas las peticiones y respuestas.

### 1.5 Idioma de errores

Los mensajes de error van en español de España:
```json
{
  "detail": "Token inválido o expirado"
}
```

### 1.6 XSS y PII

- Todos los campos de texto en respuestas se escapan contra XSS (`html.escape`).
- Datos personales sensibles (DNI, NIE, nº SS, IBAN, teléfono, email) se **enmascaran** en respuestas normales.
- El campo `pin_hash` **nunca** se expone en respuestas de la API.

---

## 2. Autenticación

### 2.1 Esquema

| Tipo | Header |
|------|--------|
| **JWT Bearer** | `Authorization: Bearer <access_token>` |
| **Device Token** | `Authorization: Bearer <device_token>` (solo terminales ESP32) |

### 2.2 Cookies httpOnly

El backend también puede leer el JWT de cookies httpOnly:
```
Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/
Set-Cookie: refresh_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/
```

### 2.3 Roles y permisos

| Rol | Permisos |
|-----|----------|
| `super_admin` | Acceso global a todos los tenants |
| `owner` | Gestión completa de su tenant |
| `manager` | Operaciones diarias, fichaje, informes |
| `employee` | No tiene login API (solo ficha desde terminal) |
| `device` | Terminal ESP32 (token propio, solo `/api/clock/*`) |

### 2.4 Claims del JWT

```json
{
  "sub": "user-uuid",
  "email": "owner@restaurante.com",
  "role": "owner",
  "tenant_id": "tenant-uuid",
  "type": "access",
  "exp": 1234567890
}
```

| Claim | Descripción |
|-------|-------------|
| `sub` | ID del usuario |
| `email` | Email del usuario |
| `role` | `super_admin`, `owner`, `manager` |
| `tenant_id` | ID del tenant (null para super_admin) |
| `type` | `access` o `refresh` |
| `exp` | Timestamp de expiración (Unix) |

---

## 3. Rate limiting

### 3.1 Middleware global (RateLimitMiddleware)

Sliding window por (IP, path):

| Endpoint | Límite | Ventana |
|----------|--------|---------|
| `/api/auth/login` | 10 req/min | 60s |
| `/api/clock` | 30 req/min | 60s |
| `/api/clock/nfc` | 30 req/min | 60s |
| `/api/employees` | 60 req/min | 60s |
| Default (resto) | 100 req/min | 60s |

**Respuesta 429:**
```json
{
  "detail": "Rate limit exceeded. Intentelo mas tarde."
}
```
Headers: `Retry-After: 60`

### 3.2 Rate limiting de auth (Redis-backed)

| Endpoint | Límite | Ventana |
|----------|--------|---------|
| `POST /api/auth/login` | 10 intentos | 5 min (300s) |
| `POST /api/auth/register` | 3 intentos | 1 hora (3600s) |

### 3.3 Rate limiting de fichaje (PIN)

| Endpoint | Límite | Ventana |
|----------|--------|---------|
| `POST /api/clock` (PIN fail) | Configurable | Bloqueo de PIN por N minutos |
| `POST /api/clock/nfc` | 30/min | 60s |
| Fichaje por tenant | Configurable | 1 hora |

---

## 4. Paginación

Todos los endpoints `GET` de listado soportan paginación offset/limit:

### 4.1 Parámetros de query

| Parámetro | Tipo | Default | Rango |
|-----------|------|---------|-------|
| `page` | int | 1 | ≥ 1 |
| `limit` | int | 50 | 1–500 |

### 4.2 Envelope de respuesta

```json
{
  "items": [...],
  "total": 127,
  "page": 1,
  "limit": 50,
  "pages": 3
}
```

| Campo | Descripción |
|-------|-------------|
| `items` | Array de objetos de la página actual |
| `total` | Total de registros que cumplen los filtros |
| `page` | Página actual (1-indexed) |
| `limit` | Items por página |
| `pages` | Total de páginas (`ceil(total / limit)`) |

---

## 5. Modelos de respuesta

### 5.1 Respuesta de error estándar

```json
{
  "detail": "Mensaje de error descriptivo"
}
```

### 5.2 Respuesta de éxito de creación

```json
{
  "id": "uuid",
  "field1": "valor",
  "field2": 123,
  "created_at": "2026-08-09T14:30:00+00:00"
}
```

### 5.3 Respuesta de eliminación

Status `204 No Content` — sin body.

---

## 6. Dominio: Auth

**Router:** `app/routers/auth.py`  
**Prefijo:** `/api/auth`  
**Tag:** `Auth`

### 6.1 POST /api/auth/login

Autentica un usuario y devuelve access + refresh tokens.

**Request body:**
```json
{
  "email": "owner@restaurante.com",
  "password": "miPassword123"
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "owner@restaurante.com",
    "name": "Juan García",
    "role": "owner",
    "tenant_id": "uuid"
  }
}
```

**Códigos de estado:**

| Código | Descripción |
|--------|-------------|
| 200 | Login correcto |
| 401 | Email o contraseña incorrectos |
| 429 | Rate limit excedido (10 intentos / 5 min) |

**Rate limit:** 10 intentos por 5 minutos por IP.

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@restaurante.com",
    "password": "miPassword123"
  }'
```

---

### 6.2 POST /api/auth/register

Registra un nuevo tenant + owner. Solo accesible si no hay super_admin o por super_admin existente.

**Request body:**
```json
{
  "restaurant_name": "Bar La Plaza",
  "owner_name": "Juan García",
  "email": "owner@barlaplaza.com",
  "password": "miPassword123",
  "phone": "+34 600 123 456"
}
```

**Validaciones:**
- `password`: mínimo 6 caracteres
- `email`: debe ser único
- Rate limit: 3 registros por hora por IP

**Response 201:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "owner@barlaplaza.com",
    "name": "Juan García",
    "role": "owner",
    "tenant_id": "uuid"
  }
}
```

**Códigos de estado:**

| Código | Descripción |
|--------|-------------|
| 201 | Registro correcto |
| 400 | Email ya registrado / contraseña demasiado corta |
| 429 | Rate limit excedido (3 registros / hora) |

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_name": "Bar La Plaza",
    "owner_name": "Juan García",
    "email": "owner@barlaplaza.com",
    "password": "miPassword123",
    "phone": "+34 600 123 456"
  }'
```

---

### 6.3 POST /api/auth/refresh

Renueva el access token usando un refresh token válido.

**Request body:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Códigos de estado:**

| Código | Descripción |
|--------|-------------|
| 200 | Token renovado |
| 401 | Refresh token inválido o expirado |
| 403 | Refresh token revocado |

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJ..."}'
```

---

### 6.4 GET /api/auth/me

Devuelve la información del usuario autenticado.

**Auth requerida:** Bearer JWT (cualquier rol)

**Response 200:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "email": "owner@restaurante.com",
  "name": "Juan García",
  "role": "owner",
  "is_active": true,
  "created_at": "2026-08-09T14:30:00+00:00",
  "updated_at": "2026-08-09T14:30:00+00:00"
}
```

**Códigos de estado:**

| Código | Descripción |
|--------|-------------|
| 200 | OK |
| 401 | No autenticado |

**curl:**
```bash
curl -X GET https://talentup-fichaje.up.railway.app/api/auth/me \
  -H "Authorization: Bearer eyJ..."
```

---

### 6.5 POST /api/auth/logout

Cierra sesión, revoca el refresh token y limpia las cookies httpOnly.

**Auth requerida:** Bearer JWT (opcional — lee de cookie si no hay header)

**Response 200:**
```json
{
  "message": "Sesión cerrada correctamente"
}
```

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/auth/logout \
  -H "Authorization: Bearer eyJ..."
```

---

## 7. Dominio: Tenants

**Router:** `app/routers/tenants.py`  
**Prefijo:** `/api/tenants`  
**Tag:** `tenants`  
**Auth:** `super_admin` en todos los endpoints

### 7.1 GET /api/tenants

Lista todos los tenants (paginado).

**Auth:** `super_admin`

**Query params:**

| Parámetro | Tipo | Default |
|-----------|------|---------|
| `page` | int | 1 |
| `limit` | int | 50 |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Bar La Plaza",
      "legal_name": "Bar La Plaza SL",
      "cif": "B12345678",
      "plan": "basic",
      "subscription_status": "active",
      "is_active": true,
      "max_employees": 50,
      "created_at": "2026-08-09T14:30:00+00:00"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/tenants?page=1&limit=50" \
  -H "Authorization: Bearer eyJ..."
```

---

### 7.2 GET /api/tenants/{tenant_id}

Obtiene un tenant por ID.

**Auth:** `super_admin`

**Path params:**

| Parámetro | Tipo |
|-----------|------|
| `tenant_id` | UUID |

**Response 200:** Objeto Tenant completo (ver modelo en `ARCHITECTURE.md`).

**Códigos de estado:** 200, 404 (no encontrado)

**curl:**
```bash
curl -X GET https://talentup-fichaje.up.railway.app/api/tenants/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJ..."
```

---

### 7.3 POST /api/tenants

Crea un nuevo tenant.

**Auth:** `super_admin`

**Request body:**
```json
{
  "name": "Restaurante El Puerto",
  "legal_name": "Restaurante El Puerto SL",
  "cif": "B87654321",
  "address": "Calle Mayor 25",
  "phone": "+34 955 123 456",
  "email": "info@elpuerto.com",
  "convenio": "hosteleria",
  "tolerancia_min": 5,
  "plan": "basic"
}
```

**Response 201:** Objeto Tenant creado.

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/tenants \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Restaurante El Puerto",
    "cif": "B87654321",
    "convenio": "hosteleria",
    "plan": "basic"
  }'
```

---

### 7.4 PUT /api/tenants/{tenant_id}

Actualiza un tenant existente.

**Auth:** `super_admin`

**Request body (todos opcionales):**
```json
{
  "name": "Restaurante El Puerto (actualizado)",
  "plan": "pro",
  "is_active": false,
  "tolerancia_min": 10
}
```

**Response 200:** Objeto Tenant actualizado.

**curl:**
```bash
curl -X PUT https://talentup-fichaje.up.railway.app/api/tenants/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"plan": "pro", "is_active": false}'
```

---

### 7.5 DELETE /api/tenants/{tenant_id}

Elimina un tenant (soft delete → `is_active = false` o hard delete).

**Auth:** `super_admin`

**Response:** `204 No Content`

**curl:**
```bash
curl -X DELETE https://talentup-fichaje.up.railway.app/api/tenants/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJ..."
```

---

## 8. Dominio: Employees

**Router:** `app/routers/employees.py`  
**Prefijo:** `/api/employees`  
**Tag:** `employees`  
**Auth:** `require_owner` (super_admin, owner)

### 8.1 GET /api/employees

Lista empleados del tenant (paginado).

**Auth:** `require_owner`

**Query params:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `page` | int | 1 | Página |
| `limit` | int | 50 | Items por página (max 500) |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_code": "EMP001",
      "name": "María",
      "last_name": "López",
      "dni": "***5678A",
      "phone": "*** 345 678",
      "email": "m***@email.com",
      "categoria_profesional": "Cocinero",
      "tipo_contrato": "indefinido",
      "shift_id": "uuid",
      "clock_method": "nfc",
      "estado": "activo",
      "is_active": true,
      "saldo_vacaciones": 22.5,
      "created_at": "2026-08-09T14:30:00+00:00"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

> **Nota PII:** DNI, teléfono, email, IBAN vienen enmascarados en la respuesta normal.

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/employees?page=1&limit=50" \
  -H "Authorization: Bearer eyJ..."
```

---

### 8.2 GET /api/employees/{employee_id}

Obtiene un empleado por ID.

**Auth:** `require_owner`

**Path params:**

| Parámetro | Tipo |
|-----------|------|
| `employee_id` | UUID |

**Response 200:** Objeto Employee completo (con PII enmascarado).

**Códigos de estado:** 200, 404

**curl:**
```bash
curl -X GET https://talentup-fichaje.up.railway.app/api/employees/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJ..."
```

---

### 8.3 POST /api/employees

Crea un nuevo empleado.

**Auth:** `require_owner`

**Request body (campos clave):**
```json
{
  "name": "María",
  "last_name": "López",
  "dni": "12345678A",
  "nie": null,
  "numero_ss": "123456789012",
  "phone": "+34 600 123 456",
  "email": "maria@email.com",
  "categoria_profesional": "Cocinero",
  "tipo_contrato": "indefinido",
  "fecha_alta": "2026-01-15",
  "tipo_jornada": "completa",
  "horas_semanales": 40,
  "horas_diarias": 8,
  "pin": "1234",
  "nfc_card_id": "A1B2C3D4",
  "nfc_uid": "04A3B2C1",
  "shift_id": "uuid-del-turno",
  "clock_method": "nfc",
  "vacation_annual_days": 30,
  "coste_hora": 12.50,
  "iban": "ES1234567890123456789012",
  "food_handling_cert": true,
  "food_handling_expiry": "2027-01-15",
  "estado": "activo",
  "is_active": true
}
```

> **Seguridad:** El `pin` se hashea con bcrypt + SHA-256 antes de almacenarse. Nunca se devuelve en respuestas.

**Response 201:** Objeto Employee creado (sin `pin_hash`).

**Códigos de estado:**

| Código | Descripción |
|--------|-------------|
| 201 | Empleado creado |
| 400 | Validación fallida |
| 403 | No autorizado (no es owner) |

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/employees \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "María",
    "last_name": "López",
    "dni": "12345678A",
    "categoria_profesional": "Cocinero",
    "tipo_contrato": "indefinido",
    "pin": "1234",
    "nfc_uid": "04A3B2C1",
    "shift_id": "uuid-del-turno",
    "clock_method": "nfc"
  }'
```

---

### 8.4 PUT /api/employees/{employee_id}

Actualiza un empleado. Todos los campos son opcionales.

**Auth:** `require_owner`

**Request body (ejemplo):**
```json
{
  "categoria_profesional": "Jefe de Cocina",
  "coste_hora": 15.00,
  "shift_id": "nuevo-uuid-turno",
  "pin": "5678"
}
```

**Response 200:** Objeto Employee actualizado.

**curl:**
```bash
curl -X PUT https://talentup-fichaje.up.railway.app/api/employees/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"coste_hora": 15.00, "pin": "5678"}'
```

---

### 8.5 DELETE /api/employees/{employee_id}

Elimina un empleado.

**Auth:** `require_owner`

**Response:** `204 No Content`

**curl:**
```bash
curl -X DELETE https://talentup-fichaje.up.railway.app/api/employees/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJ..."
```

---

## 9. Dominio: Shifts

**Router:** `app/routers/shifts.py`  
**Prefijo:** `/api/shifts`  
**Tag:** `shifts`  
**Auth:** `require_owner`

### 9.1 GET /api/shifts

Lista turnos del tenant (paginado).

**Query params:** `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "name": "Mañana",
      "code": "M",
      "shift_type": "morning",
      "start_time": "08:00",
      "end_time": "16:00",
      "break_start": "12:00",
      "break_end": "13:00",
      "break_min": 60,
      "total_hours": 8.0,
      "tolerance_min": 5,
      "grace_period_min": 15,
      "is_split": false,
      "is_night": false,
      "plus_nocturnidad": 0,
      "plus_festividad": 0,
      "is_rotativo": false,
      "color": "#FF6B35",
      "is_active": true,
      "sort_order": 0
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/shifts?page=1&limit=50" \
  -H "Authorization: Bearer eyJ..."
```

---

### 9.2 GET /api/shifts/{shift_id}

Obtiene un turno por ID.

**Response 200:** Objeto Shift.

**Códigos de estado:** 200, 404

---

### 9.3 POST /api/shifts

Crea un nuevo turno.

**Request body:**
```json
{
  "name": "Tarde",
  "code": "T",
  "shift_type": "afternoon",
  "start_time": "16:00",
  "end_time": "00:00",
  "break_start": "20:00",
  "break_end": "21:00",
  "break_min": 60,
  "tolerance_min": 5,
  "grace_period_min": 15,
  "is_night": false,
  "plus_nocturnidad": 0,
  "is_rotativo": false,
  "color": "#007AFF"
}
```

**Validaciones:**
- `start_time`, `end_time`: formato `HH:MM` (regex `^([01]\d|2[0-3]):([0-5]\d)$`)

**Response 201:** Objeto Shift creado.

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/shifts \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tarde",
    "shift_type": "afternoon",
    "start_time": "16:00",
    "end_time": "00:00",
    "color": "#007AFF"
  }'
```

---

### 9.4 PUT /api/shifts/{shift_id}

Actualiza un turno. Todos los campos opcionales.

**Response 200:** Objeto Shift actualizado.

---

### 9.5 DELETE /api/shifts/{shift_id}

Elimina un turno.

**Response:** `204 No Content`

---

## 10. Dominio: Schedules

**Router:** `app/routers/schedules.py`  
**Prefijo:** `/api/schedules`  
**Tag:** `schedules`  
**Auth:** `require_owner`

### 10.1 GET /api/schedules

Lista asignaciones de horario (paginado).

**Query params:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `employee_id` | UUID | Filtrar por empleado |
| `date_from` | string | Fecha inicio (YYYY-MM-DD) |
| `date_to` | string | Fecha fin (YYYY-MM-DD) |
| `page` | int | Página (default 1) |
| `limit` | int | Items por página (default 50, max 500) |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_id": "uuid",
      "shift_id": "uuid",
      "date": "2026-08-09",
      "notes": "Turno partido por evento",
      "created_at": "2026-08-09T14:30:00+00:00"
    }
  ],
  "total": 30,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/schedules?date_from=2026-08-01&date_to=2026-08-31&page=1&limit=50" \
  -H "Authorization: Bearer eyJ..."
```

---

### 10.2 GET /api/schedules/{schedule_id}

Obtiene una asignación por ID.

**Response 200:** Objeto Schedule.

---

### 10.3 POST /api/schedules

Crea una asignación empleado-turno-fecha.

**Request body:**
```json
{
  "employee_id": "uuid",
  "shift_id": "uuid",
  "date": "2026-08-09",
  "notes": "Cubre a María"
}
```

> **Constraint:** UniqueConstraint `(tenant_id, employee_id, date)` — no se puede asignar dos turnos al mismo empleado en la misma fecha.

**Response 201:** Objeto Schedule creado.

**Códigos de estado:** 201, 400 (duplicado), 409 (conflicto de unique constraint)

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/schedules \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "550e8400-e29b-41d4-a716-446655440000",
    "shift_id": "660e8400-e29b-41d4-a716-446655440000",
    "date": "2026-08-09"
  }'
```

---

### 10.4 PUT /api/schedules/{schedule_id}

Actualiza una asignación (cambiar turno o notas).

**Request body:**
```json
{
  "shift_id": "nuevo-uuid-turno",
  "notes": "Cambio de turno"
}
```

**Response 200:** Objeto Schedule actualizado.

---

### 10.5 DELETE /api/schedules/{schedule_id}

Elimina una asignación.

**Response:** `204 No Content`

---

## 11. Dominio: Clock Events (Fichajes)

**Router:** `app/routers/clock.py`  
**Prefijo:** `/api/clock`  
**Tag:** `clock`  
**Auth:** Varía por endpoint (JWT o device token)

### 11.1 GET /api/clock/tenants

Lista tenants disponibles para el terminal (info de selección).

**Auth:** Device token o `require_manager`

---

### 11.2 POST /api/clock

Fichaje por PIN desde el terminal o dashboard.

**Auth:** `require_manager` (JWT) o device token

**Request body:**
```json
{
  "tenant_id": "uuid",
  "pin": "1234",
  "type": "in",
  "latitude": 41.3851,
  "longitude": 2.1734,
  "is_offline": false
}
```

| Campo | Tipo | Valores |
|-------|------|---------|
| `tenant_id` | UUID | ID del tenant |
| `pin` | string | PIN del empleado |
| `type` | string | `in`, `out`, `break_start`, `break_end` |
| `latitude` | float | Opcional (geolocalización) |
| `longitude` | float | Opcional |
| `is_offline` | bool | Si el fichaje fue offline |

**Response 201:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "employee_id": "uuid",
  "type": "in",
  "timestamp": "2026-08-09T14:30:00+00:00",
  "employee_name": "María López",
  "message": "Fichaje de entrada registrado"
}
```

**Códigos de estado:**

| Código | Descripción |
|--------|-------------|
| 201 | Fichaje registrado |
| 400 | PIN inválido / tipo no válido |
| 404 | Empleado no encontrado |
| 429 | Rate limit (PIN bloqueado) |

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/clock \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "pin": "1234",
    "type": "in"
  }'
```

---

### 11.3 POST /api/clock/nfc

Fichaje por NFC desde el terminal ESP32.

**Auth:** Device token (`Authorization: Bearer {device_token}`)

**Request body:**
```json
{
  "tenant_id": "uuid",
  "nfc_uid": "04A3B2C1",
  "type": "in",
  "is_offline": false,
  "synced_at": "2026-08-09T14:30:00+00:00"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "employee_id": "uuid",
  "type": "in",
  "timestamp": "2026-08-09T14:30:00+00:00",
  "employee_name": "María López",
  "message": "Fichaje NFC registrado"
}
```

**Códigos de estado:**

| Código | Descripción |
|--------|-------------|
| 201 | Fichaje NFC registrado |
| 401 | Device token inválido |
| 403 | Device desactivado |
| 404 | Empleado con ese NFC no encontrado |

**curl (terminal ESP32):**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/clock/nfc \
  -H "Authorization: Bearer {device_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "nfc_uid": "04A3B2C1",
    "type": "in"
  }'
```

---

### 11.4 POST /api/clock/qr

Fichaje por código QR.

**Auth:** Device token

**Request body:**
```json
{
  "tenant_id": "uuid",
  "qr_data": "encoded-qr-data",
  "type": "in"
}
```

**Response 201:** Igual que `/api/clock/nfc`.

---

### 11.5 GET /api/clock/history

Historial de fichajes (paginado).

**Auth:** `require_manager`

**Query params:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `employee_id` | UUID | Filtrar por empleado |
| `date_from` | string | Fecha inicio (YYYY-MM-DD) |
| `date_to` | string | Fecha fin (YYYY-MM-DD) |
| `type` | string | Filtrar por tipo (in, out, break_start, break_end) |
| `page` | int | Página (default 1) |
| `limit` | int | Items por página (default 50, max 500) |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_id": "uuid",
      "type": "in",
      "timestamp": "2026-08-09T08:00:00+00:00",
      "latitude": 41.3851,
      "longitude": 2.1734,
      "is_offline": false,
      "is_cancelled": false
    }
  ],
  "total": 500,
  "page": 1,
  "limit": 50,
  "pages": 10
}
```

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/clock/history?date_from=2026-08-01&date_to=2026-08-31&page=1&limit=50" \
  -H "Authorization: Bearer eyJ..."
```

---

### 11.6 GET /api/clock/today

Fichajes del día actual.

**Auth:** `require_manager`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "employee_id": "uuid",
      "employee_name": "María López",
      "type": "in",
      "timestamp": "2026-08-09T08:00:00+00:00"
    }
  ]
}
```

---

### 11.7 POST /api/clock/{clock_id}/cancel

Anula un fichaje (con motivo). El registro original se preserva (inmutable).

**Auth:** `require_manager`

**Request body:**
```json
{
  "cancel_reason": "Fichaje erróneo - se equivocó de empleado"
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "is_cancelled": true,
  "cancel_reason": "Fichaje erróneo - se equivocó de empleado",
  "cancelled_by": "uuid-user",
  "cancelled_at": "2026-08-09T15:00:00+00:00"
}
```

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/clock/550e8400-e29b-41d4-a716-446655440000/cancel \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"cancel_reason": "Fichaje erróneo"}'
```

---

## 12. Dominio: Incidents

**Router:** `app/routers/incidents.py`  
**Prefijo:** `/api/incidents`  
**Tag:** `incidents`  
**Auth:** `require_manager`

### 12.1 GET /api/incidents

Lista incidencias del tenant (paginado).

**Query params:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `date_from` | string | Fecha inicio (YYYY-MM-DD) |
| `date_to` | string | Fecha fin (YYYY-MM-DD) |
| `employee_id` | UUID | Filtrar por empleado |
| `incident_type` | string | Filtrar por tipo |
| `page` | int | Página (default 1) |
| `limit` | int | Items por página (default 50, max 500) |

**Tipos de incidencia:** `no_clock_in`, `no_clock_out`, `late_arrival`, `early_leave`, `missed_break`, `clock_outside_shift`, `duplicate_clock`, `missing_break`, `overtime_unauthorized`, `schedule_mismatch`, `offline_clock`, `manual`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_id": "uuid",
      "date": "2026-08-09",
      "incident_type": "late_arrival",
      "description": "Llegó 15 min tarde al turno de mañana",
      "severity": "warning",
      "is_resolved": false,
      "source": "auto",
      "created_at": "2026-08-09T08:15:00+00:00"
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/incidents?date_from=2026-08-01&date_to=2026-08-31&incident_type=late_arrival" \
  -H "Authorization: Bearer eyJ..."
```

---

### 12.2 POST /api/incidents/detect

Ejecuta la detección automática de incidencias (background task).

**Auth:** `require_manager`

**Request body:**
```json
{
  "target_date": "2026-08-09"
}
```

**Response 200:**
```json
{
  "message": "Detección de incidencias iniciada para 2026-08-09",
  "job_id": "uuid"
}
```

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/incidents/detect \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-08-09"}'
```

---

### 12.3 PATCH /api/incidents/{incident_id}/resolve

Marca una incidencia como resuelta.

**Auth:** `require_manager`

**Request body:**
```json
{
  "resolution": "Empleado justificó el retraso con certificado médico"
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "is_resolved": true,
  "resolution": "Empleado justificó el retraso con certificado médico",
  "resolved_by": "uuid-user",
  "resolved_at": "2026-08-09T16:00:00+00:00"
}
```

**curl:**
```bash
curl -X PATCH https://talentup-fichaje.up.railway.app/api/incidents/550e8400-e29b-41d4-a716-446655440000/resolve \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"resolution": "Justificado con certificado médico"}'
```

---

## 13. Dominio: Contracts

**Router:** `app/routers/contracts.py`  
**Prefijo:** `/api/contracts`  
**Tag:** `contracts`  
**Auth:** `require_owner`

### 13.1 GET /api/contracts

Lista contratos (paginado).

**Query params:** `employee_id`, `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_id": "uuid",
      "contract_type": "indefinido",
      "category": "Cocinero",
      "start_date": "2026-01-15",
      "end_date": null,
      "is_indefinite": true,
      "weekly_hours": 40,
      "daily_hours": 8,
      "salary_base": 1500.00,
      "salary_extras": 200.00,
      "prorated_pages": 150.00
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 13.2 GET /api/contracts/{contract_id}

Obtiene un contrato por ID.

---

### 13.3 POST /api/contracts

Crea un contrato.

**Request body:**
```json
{
  "employee_id": "uuid",
  "contract_type": "temporal",
  "category": "Ayudante",
  "start_date": "2026-06-01",
  "end_date": "2026-09-30",
  "duration_days": 122,
  "is_indefinite": false,
  "weekly_hours": 40,
  "daily_hours": 8,
  "salary_base": 1200.00,
  "salary_extras": 150.00,
  "prorated_pages": 125.00,
  "document_url": "https://...",
  "signed_date": "2026-05-28",
  "notes": "Contrato de verano"
}
```

**Response 201:** Objeto Contract creado.

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/contracts \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "uuid",
    "contract_type": "temporal",
    "start_date": "2026-06-01",
    "end_date": "2026-09-30",
    "weekly_hours": 40,
    "salary_base": 1200.00
  }'
```

---

### 13.4 PUT /api/contracts/{contract_id}

Actualiza un contrato.

---

### 13.5 DELETE /api/contracts/{contract_id}

Elimina un contrato.

**Response:** `204 No Content`

---

## 14. Dominio: Holidays

**Router:** `app/routers/holidays.py`  
**Prefijo:** `/api/holidays`  
**Tag:** `holidays`  
**Auth:** `require_owner`

### 14.1 GET /api/holidays

Lista festivos (paginado).

**Query params:** `year`, `type` (national/regional/local), `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "date": "2026-08-15",
      "name": "Asunción de la Virgen",
      "type": "national",
      "region": null,
      "locality": null,
      "is_paid": true,
      "is_working": false,
      "year": 2026
    }
  ],
  "total": 14,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 14.2 GET /api/holidays/{holiday_id}

Obtiene un festivo por ID.

---

### 14.3 POST /api/holidays

Crea un festivo.

**Request body:**
```json
{
  "date": "2026-12-25",
  "name": "Navidad",
  "type": "national",
  "region": null,
  "locality": null,
  "is_paid": true,
  "is_working": false,
  "year": 2026
}
```

**Response 201:** Objeto Holiday creado.

---

### 14.4 PUT /api/holidays/{holiday_id}

Actualiza un festivo.

---

### 14.5 DELETE /api/holidays/{holiday_id}

Elimina un festivo.

**Response:** `204 No Content`

---

## 15. Dominio: Vacations

**Router:** `app/routers/vacations.py`  
**Prefijo:** `/api/vacations`  
**Tag:** `vacations`  
**Auth:** `require_owner`

### 15.1 GET /api/vacations

Lista solicitudes de vacaciones (paginado).

**Query params:** `employee_id`, `status` (pending/approved/rejected), `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_id": "uuid",
      "type": "vacation",
      "start_date": "2026-08-15",
      "end_date": "2026-08-25",
      "total_days": 7,
      "days_count_method": "working",
      "status": "pending",
      "reason": "Vacaciones de verano",
      "supporting_doc_url": null
    }
  ],
  "total": 8,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 15.2 GET /api/vacations/{vacation_id}

Obtiene una solicitud por ID.

---

### 15.3 POST /api/vacations

Crea una solicitud de vacaciones.

**Request body:**
```json
{
  "employee_id": "uuid",
  "type": "vacation",
  "start_date": "2026-08-15",
  "end_date": "2026-08-25",
  "total_days": 7,
  "days_count_method": "working",
  "reason": "Vacaciones de verano",
  "supporting_doc_url": null
}
```

**Response 201:** Objeto VacationRequest creado.

---

### 15.4 POST /api/vacations/{vacation_id}/approve

Aprueba una solicitud de vacaciones.

**Request body:**
```json
{
  "reason": "Aprobado por encargado"
}
```

**Response 200:** Objeto VacationRequest con `status: "approved"`.

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/vacations/550e8400-e29b-41d4-a716-446655440000/approve \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"reason": "Aprobado"}'
```

---

### 15.5 POST /api/vacations/{vacation_id}/reject

Rechaza una solicitud de vacaciones.

**Request body:**
```json
{
  "reason": "No hay cobertura para esas fechas"
}
```

**Response 200:** Objeto VacationRequest con `status: "rejected"`.

---

## 16. Dominio: Leave (Bajas IT)

**Router:** `app/routers/leave.py`  
**Prefijo:** `/api/leave`  
**Tag:** `leave`  
**Auth:** `require_owner`

### 16.1 GET /api/leave

Lista bajas IT (paginado).

**Query params:** `employee_id`, `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_id": "uuid",
      "leave_type": "enfermedad",
      "start_date": "2026-08-01",
      "end_date": "2026-08-07",
      "expected_end_date": "2026-08-07",
      "total_days": 7,
      "diagnosis_code": "J00",
      "medical_center": "Centro de Salud El Carmen",
      "doctor_name": "Dr. Pérez",
      "part_number": 1,
      "mutua": "Mutua Universal",
      "is_work_accident": false,
      "is_professional_illness": false,
      "document_url": "https://..."
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 16.2 GET /api/leave/{leave_id}

Obtiene una baja por ID.

---

### 16.3 POST /api/leave

Crea una baja IT.

**Request body:**
```json
{
  "employee_id": "uuid",
  "leave_type": "enfermedad",
  "start_date": "2026-08-01",
  "end_date": "2026-08-07",
  "expected_end_date": "2026-08-07",
  "total_days": 7,
  "diagnosis_code": "J00",
  "medical_center": "Centro de Salud El Carmen",
  "doctor_name": "Dr. Pérez",
  "part_number": 1,
  "mutua": "Mutua Universal",
  "is_work_accident": false,
  "is_professional_illness": false,
  "document_url": "https://..."
}
```

**Response 201:** Objeto Leave creado.

---

### 16.4 PUT /api/leave/{leave_id}

Actualiza una baja (ej: prorroga con nuevo parte).

---

### 16.5 DELETE /api/leave/{leave_id}

Elimina una baja.

**Response:** `204 No Content`

---

## 17. Dominio: Overtime (Horas Extra)

**Router:** `app/routers/overtime.py`  
**Prefijo:** `/api/overtime`  
**Tag:** `overtime`  
**Auth:** `require_owner`

### 17.1 GET /api/overtime

Lista horas extra (paginado).

**Query params:** `employee_id`, `compensation_type`, `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_id": "uuid",
      "date": "2026-08-09",
      "shift_id": "uuid",
      "overtime_type": "structural",
      "total_minutes": 60,
      "compensated_minutes": 0,
      "paid_minutes": 60,
      "hourly_rate_multiplier": 1.75,
      "hourly_rate": 21.88,
      "overtime_amount": 21.88,
      "notes": "Horas extra por evento"
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 17.2 GET /api/overtime/{overtime_id}

Obtiene un registro de horas extra por ID.

---

### 17.3 POST /api/overtime

Registra horas extra manualmente.

**Request body:**
```json
{
  "employee_id": "uuid",
  "date": "2026-08-09",
  "shift_id": "uuid",
  "overtime_type": "structural",
  "total_minutes": 60,
  "compensated_minutes": 0,
  "paid_minutes": 60,
  "hourly_rate_multiplier": 1.75,
  "hourly_rate": 12.50,
  "overtime_amount": 21.88,
  "notes": "Horas extra por evento"
}
```

**Response 201:** Objeto Overtime creado.

---

### 17.4 POST /api/overtime/calculate

Calcula horas extra automáticamente a partir de fichajes.

**Request body:**
```json
{
  "employee_id": "uuid",
  "date_from": "2026-08-01",
  "date_to": "2026-08-31"
}
```

**Response 200:**
```json
{
  "employee_id": "uuid",
  "period": "2026-08-01 to 2026-08-31",
  "total_overtime_minutes": 180,
  "overtime_hours": 3.0,
  "details": [...]
}
```

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/overtime/calculate \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "550e8400-e29b-41d4-a716-446655440000",
    "date_from": "2026-08-01",
    "date_to": "2026-08-31"
  }'
```

---

## 18. Dominio: Payroll (Nóminas)

**Router:** `app/routers/payroll.py`  
**Prefijo:** `/api/payroll`  
**Tag:** `payroll`  
**Auth:** `require_owner`

### 18.1 GET /api/payroll

Lista nóminas (paginado).

**Query params:** `year`, `month`, `employee_id`, `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "employee_id": "uuid",
      "employee_name": "María López",
      "year": 2026,
      "month": 7,
      "gross_salary": 1800.00,
      "irpf_amount": 90.00,
      "ss_employee_amount": 114.30,
      "net_salary": 1595.70,
      "status": "draft"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 18.2 GET /api/payroll/{month}/{year}

Obtiene nóminas de un mes/año específico.

**Path params:**

| Parámetro | Tipo |
|-----------|------|
| `month` | int (1-12) |
| `year` | int |

**Response 200:** Array de nóminas del mes.

---

### 18.3 POST /api/payroll/close

Cierra las nóminas del mes (background task).

**Request body:**
```json
{
  "month": 7,
  "year": 2026
}
```

**Response 200:**
```json
{
  "message": "Cierre de nóminas iniciado para 07/2026",
  "job_id": "uuid"
}
```

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/payroll/close \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"month": 7, "year": 2026}'
```

---

## 19. Dominio: Notifications

**Router:** `app/routers/notifications.py`  
**Prefijo:** `/api/notifications`  
**Tag:** `notifications`  
**Auth:** `require_owner`

### 19.1 GET /api/notifications

Lista notificaciones (paginado).

**Query params:** `unread_only` (bool), `category`, `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "recipient_type": "employee",
      "employee_id": "uuid",
      "type": "incident",
      "title": "Nueva incidencia detectada",
      "message": "Llegada tarde el 2026-08-09",
      "priority": "normal",
      "category": "fichaje",
      "is_read": false,
      "sent_via": "in_app",
      "created_at": "2026-08-09T08:15:00+00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 19.2 GET /api/notifications/unread

Devuelve el conteo de notificaciones no leídas.

**Response 200:**
```json
{
  "unread_count": 5
}
```

---

### 19.3 POST /api/notifications

Crea una notificación.

**Request body:**
```json
{
  "recipient_type": "employee",
  "employee_id": "uuid",
  "type": "reminder",
  "title": "Recordatorio de turno",
  "message": "Tu turno empieza en 30 minutos",
  "priority": "normal",
  "category": "turno",
  "action_url": "/dashboard/turnos",
  "action_label": "Ver turnos",
  "sent_via": "in_app"
}
```

**Response 201:** Objeto Notification creado.

---

### 19.4 POST /api/notifications/send

Envía notificaciones pendientes (background task).

---

### 19.5 POST /api/notifications/{notification_id}/read

Marca una notificación como leída.

**Response 200:**
```json
{
  "id": "uuid",
  "is_read": true
}
```

---

### 19.6 POST /api/notifications/read-all

Marca todas las notificaciones como leídas.

**Response 200:**
```json
{
  "message": "Todas las notificaciones marcadas como leídas",
  "updated_count": 10
}
```

---

## 20. Dominio: Calendar (Calendario Laboral)

**Router:** `app/routers/calendar.py`  
**Prefijo:** `/api/calendar`  
**Tag:** `calendar`  
**Auth:** `require_owner`

### 20.1 GET /api/calendar

Obtiene el calendario laboral de un año (paginado).

**Query params:** `year` (obligatorio), `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "year": 2026,
      "date": "2026-08-09",
      "day_type": "working",
      "is_working_day": true,
      "opening_time": "08:00",
      "closing_time": "00:00",
      "requires_special_schedule": false,
      "notes": null
    }
  ],
  "total": 365,
  "page": 1,
  "limit": 366,
  "pages": 1
}
```

---

### 20.2 POST /api/calendar/generate

Genera el calendario laboral para un año, marcando fines de semana y festivos.

**Query params:** `year` (obligatorio)

**Response 201:**
```json
{
  "message": "Calendario 2026 generado",
  "year": 2026,
  "days_generated": 365
}
```

**curl:**
```bash
curl -X POST "https://talentup-fichaje.up.railway.app/api/calendar/generate?year=2026" \
  -H "Authorization: Bearer eyJ..."
```

---

### 20.3 PUT /api/calendar/{calendar_id}

Actualiza un día del calendario.

**Request body:**
```json
{
  "day_type": "holiday",
  "is_working_day": false,
  "opening_time": null,
  "closing_time": null,
  "requires_special_schedule": false,
  "notes": "Festivo nacional"
}
```

---

## 21. Dominio: Settings

**Router:** `app/routers/settings.py`  
**Prefijo:** `/api/settings`  
**Tag:** `settings`  
**Auth:** `get_current_user` (GET), `require_owner` (PUT)

### 21.1 GET /api/settings

Obtiene la configuración del tenant actual.

**Auth:** Cualquier usuario autenticado

**Response 200:** Objeto Tenant completo (ver modelo en `ARCHITECTURE.md`).

```json
{
  "id": "uuid",
  "name": "Bar La Plaza",
  "convenio": "hosteleria",
  "ccaa": "Cataluña",
  "locality": "Barcelona",
  "tolerancia_min": 5,
  "vacation_days_per_year": 30,
  "payroll_day": 30,
  "payroll_period": "monthly",
  "irpf_default": 10.0,
  "ss_employee_percent": 6.35,
  "ss_company_percent": 29.90,
  "plan": "basic",
  "setup_completed": true,
  ...
}
```

---

### 21.2 PUT /api/settings

Actualiza la configuración del tenant.

**Auth:** `require_owner`

**Request body (todos opcionales):**
```json
{
  "name": "Bar La Plaza (actualizado)",
  "legal_name": "Bar La Plaza SL",
  "cif": "B12345678",
  "address": "Calle Mayor 25",
  "convenio": "hosteleria",
  "ccaa": "Cataluña",
  "locality": "Barcelona",
  "tolerancia_min": 10,
  "vacation_days_per_year": 30,
  "weekly_hours": 40,
  "work_days": 5,
  "notif_email": "owner@barlaplaza.com",
  "notif_clock": 5,
  "notif_vacation": "email",
  "setup_completed": true
}
```

**Response 200:** Objeto Tenant actualizado.

**curl:**
```bash
curl -X PUT https://talentup-fichaje.up.railway.app/api/settings \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"tolerancia_min": 10, "setup_completed": true}'
```

---

## 22. Dominio: Billing (Stripe)

**Router:** `app/routers/billing.py`  
**Prefijo:** `/api/billing`  
**Tag:** `billing`  
**Auth:** `require_owner`

### 22.1 POST /api/billing/checkout-session

Crea una Stripe Checkout Session para suscripción.

**Request body:**
```json
{
  "plan": "basic",
  "tenant_id": "uuid",
  "success_url": "https://talentup.es/dashboard?checkout=success",
  "cancel_url": "https://talentup.es/dashboard?checkout=cancel"
}
```

| Plan | Price ID env var |
|------|------------------|
| `basic` | `STRIPE_PRICE_BASIC` |
| `pro` | `STRIPE_PRICE_PRO` |
| `kit` | `STRIPE_PRICE_KIT` |

**Response 200:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/sess_...",
  "session_id": "cs_test_..."
}
```

**Códigos de estado:**

| Código | Descripción |
|--------|-------------|
| 200 | Session creada |
| 400 | Plan no válido |
| 503 | Stripe no configurado |

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/billing/checkout-session \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "basic",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "success_url": "https://talentup.es/dashboard?checkout=success",
    "cancel_url": "https://talentup.es/dashboard?checkout=cancel"
  }'
```

---

### 22.2 POST /api/billing/webhook

Recibe webhooks de Stripe. **No requiere auth JWT** — valida con `STRIPE_WEBHOOK_SECRET`.

**Headers:**
```
Stripe-Signature: t=...,v1=...,v0=...
```

**Eventos soportados:**
- `checkout.session.completed`
- `invoice.paid`
- `customer.subscription.updated`
- `customer.subscription.deleted`

**Response 200:**
```json
{
  "received": true
}
```

**curl (simulación):**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/billing/webhook \
  -H "Stripe-Signature: t=123,v1=abc" \
  -H "Content-Type: application/json" \
  -d '{"type": "invoice.paid", "data": {...}}'
```

> En producción, Stripe envía el webhook directamente. No se puede probar con curl sin un payload firmado válido.

---

### 22.3 GET /api/billing/status/{tenant_id}

Obtiene el estado de la suscripción de un tenant.

**Response 200:**
```json
{
  "plan": "basic",
  "subscription_status": "active",
  "current_period_end": "2026-09-09T00:00:00+00:00",
  "stripe_customer_id": "cus_...",
  "stripe_subscription_id": "sub_..."
}
```

---

### 22.4 POST /api/billing/portal/{tenant_id}

Genera una URL del Customer Portal de Stripe para auto-gestión.

**Response 200:**
```json
{
  "portal_url": "https://billing.stripe.com/p/session_..."
}
```

---

## 23. Dominio: Devices (Terminales)

**Router:** `app/routers/devices.py`  
**Prefijo:** `/api/devices`  
**Tag:** `devices`  
**Auth:** `require_manager`

### 23.1 POST /api/devices

Registra un nuevo terminal/dispositivo para un tenant.

**Request body:**
```json
{
  "tenant_id": "uuid",
  "name": "Terminal Cocina",
  "device_token": "opcional-si-se-proporciona",
  "is_active": true
}
```

> Si no se proporciona `device_token`, se genera uno aleatorio seguro.

**Response 201:**
```json
{
  "id": 1,
  "tenant_id": "uuid",
  "device_token": "token-generado-o-proporcionado",
  "name": "Terminal Cocina",
  "is_active": true,
  "created_at": "2026-08-09T14:30:00+00:00",
  "updated_at": "2026-08-09T14:30:00+00:00"
}
```

> **Importante:** El `device_token` se devuelve **una sola vez** en la creación. Se almacena como SHA-256. El terminal ESP32 debe guardar este token.

**curl:**
```bash
curl -X POST https://talentup-fichaje.up.railway.app/api/devices \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Terminal Cocina"
  }'
```

---

## 24. Dominio: Reports (Informes)

**Router:** `app/routers/reports.py`  
**Prefijo:** `/api/reports`  
**Tag:** `reports`  
**Auth:** `require_manager`

### 24.1 GET /api/reports/hours

Horas trabajadas por empleado en un rango de fechas (paginado).

**Query params:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `employee_id` | UUID | Filtrar por empleado (opcional) |
| `date_from` | string | Fecha inicio (YYYY-MM-DD) — **obligatorio** |
| `date_to` | string | Fecha fin (YYYY-MM-DD) — **obligatorio** |
| `page` | int | Página (default 1) |
| `limit` | int | Items por página (default 50, max 500) |
| `tenant_id` | UUID | Solo super_admin: filtrar por tenant |

**Response 200:**
```json
{
  "items": [
    {
      "employee_id": "uuid",
      "employee_name": "María López",
      "total_hours": 160.5,
      "total_days": 20,
      "overtime_hours": 5.5,
      "break_hours": 20.0
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/reports/hours?date_from=2026-08-01&date_to=2026-08-31&page=1&limit=50" \
  -H "Authorization: Bearer eyJ..."
```

---

### 24.2 GET /api/reports/incidents

Informe de incidencias en un rango de fechas (paginado).

**Query params:** `date_from`, `date_to`, `employee_id`, `incident_type`, `page`, `limit`, `tenant_id` (super_admin)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "employee_id": "uuid",
      "employee_name": "María López",
      "date": "2026-08-09",
      "incident_type": "late_arrival",
      "description": "Llegó 15 min tarde",
      "severity": "warning",
      "is_resolved": false
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 24.3 GET /api/reports/export

Exporta informes en PDF o Excel. Cumple RD-ley 8/2019.

**Query params:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `format` | string | `pdf` o `excel` — **obligatorio** |
| `date_from` | string | Fecha inicio (YYYY-MM-DD) — **obligatorio** |
| `date_to` | string | Fecha fin (YYYY-MM-DD) — **obligatorio** |
| `employee_id` | UUID | Filtrar por empleado (opcional) |
| `report_type` | string | `hours`, `incidents`, `inspection` (opcional) |
| `tenant_id` | UUID | Solo super_admin |

**Response 200:**
- `Content-Type: application/pdf` → devuelve el PDF
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` → devuelve XLSX

Headers:
```
Content-Disposition: attachment; filename="informe_2026-08-01_2026-08-31.pdf"
```

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/reports/export?format=pdf&date_from=2026-08-01&date_to=2026-08-31" \
  -H "Authorization: Bearer eyJ..." \
  -o informe.pdf
```

---

### 24.4 GET /api/reports/export/async

Inicia exportación asíncrona (para informes grandes).

**Query params:** Igual que `/export` pero devuelve un `job_id`.

**Response 200:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "message": "Exportación iniciada"
}
```

---

### 24.5 GET /api/reports/export/status/{job_id}

Consulta el estado de una exportación asíncrona.

**Response 200:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "progress": 100,
  "download_url": "/api/reports/export/download/uuid"
}
```

---

### 24.6 GET /api/reports/export/download/{job_id}

Descarga el resultado de una exportación asíncrona completada.

**Response 200:** Archivo binario (PDF/XLSX).

---

### 24.7 GET /api/reports/inspection

Informe para inspección laboral (formato específico para inspección de trabajo).

**Query params:** `date_from`, `date_to`, `employee_id`, `tenant_id` (super_admin)

**Response 200:** Informe estructurado para inspección con todos los fichajes, incidencias y cálculos de horas.

**curl:**
```bash
curl -X GET "https://talentup-fichaje.up.railway.app/api/reports/inspection?date_from=2026-08-01&date_to=2026-08-31" \
  -H "Authorization: Bearer eyJ..." \
  -o inspeccion.pdf
```

---

### 24.8 GET /api/reports/absenteeism

Informe de absentismo por empleado en un periodo.

**Query params:** `date_from`, `date_to`, `employee_id`, `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "employee_id": "uuid",
      "employee_name": "María López",
      "total_absent_days": 3,
      "absenteeism_rate": 0.15,
      "reasons": {
        "enfermedad": 2,
        "personal": 1
      }
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### 24.9 GET /api/reports/labor-costs

Informe de costes laborales por empleado o por periodo.

**Query params:** `date_from`, `date_to`, `employee_id`, `page`, `limit`

**Response 200:**
```json
{
  "items": [
    {
      "employee_id": "uuid",
      "employee_name": "María López",
      "regular_hours": 160,
      "overtime_hours": 5.5,
      "regular_cost": 2000.00,
      "overtime_cost": 137.50,
      "total_cost": 2137.50,
      "plus_nocturnidad": 50.00,
      "plus_festividad": 0
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

## 25. Endpoints de sistema

### 25.1 GET /api/health

Health check de la aplicación.

**Auth:** Ninguna (público)

**Response 200:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400
}
```

---

### 25.2 GET /api/metrics

Métricas en formato Prometheus.

**Auth:** Ninguna (público — debería protegerse en producción)

**Response 200:**
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/employees",status="200"} 1250
http_requests_total{method="POST",endpoint="/api/clock",status="201"} 500
...
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/employees",le="0.05"} 1200
...
# HELP active_connections Number of HTTP requests currently being processed
# TYPE active_connections gauge
active_connections 3
```

---

### 25.3 WebSocket /ws

WebSocket para comunicación en tiempo real (estados del terminal, notificaciones push).

**Auth:** JWT en query param o header

**Eventos:**

| Evento | Dirección | Descripción |
|--------|-----------|-------------|
| `clock_event` | Server → Client | Nuevo fichaje registrado |
| `incident_detected` | Server → Client | Nueva incidencia detectada |
| `device_status` | Server → Client | Estado del terminal ESP32 |

---

## 26. Resumen de códigos de estado

| Código | Descripción | Cuándo se usa |
|--------|-------------|---------------|
| **200** | OK | GET, PUT, PATCH exitosos |
| **201** | Created | POST exitoso (creación de recurso) |
| **204** | No Content | DELETE exitoso (sin body de respuesta) |
| **400** | Bad Request | Validación fallida, formato incorrecto |
| **401** | Unauthorized | No autenticado, token inválido/expirado |
| **403** | Forbidden | Autenticado pero sin permisos suficientes |
| **404** | Not Found | Recurso no encontrado |
| **409** | Conflict | Conflicto de unique constraint |
| **429** | Too Many Requests | Rate limit excedido |
| **500** | Internal Server Error | Error no controlado |
| **503** | Service Unavailable | Dependencia no disponible (Stripe sin configurar) |

---

## Apéndice A: Resumen de routers (19 routers)

| # | Router | Prefijo | Endpoints | Auth mínima |
|---|--------|---------|-----------|-------------|
| 1 | `auth` | `/api/auth` | 5 (login, register, refresh, me, logout) | Pública / JWT |
| 2 | `employees` | `/api/employees` | 5 (CRUD) | `require_owner` |
| 3 | `shifts` | `/api/shifts` | 5 (CRUD) | `require_owner` |
| 4 | `schedules` | `/api/schedules` | 5 (CRUD) | `require_owner` |
| 5 | `clock` | `/api/clock` | 7 (+ WebSocket) | `require_manager` / device |
| 6 | `reports` | `/api/reports` | 9 | `require_manager` |
| 7 | `tenants` | `/api/tenants` | 5 (CRUD) | `require_super_admin` |
| 8 | `contracts` | `/api/contracts` | 5 (CRUD) | `require_owner` |
| 9 | `holidays` | `/api/holidays` | 5 (CRUD) | `require_owner` |
| 10 | `vacations` | `/api/vacations` | 5 (list, get, create, approve, reject) | `require_owner` |
| 11 | `leave` | `/api/leave` | 5 (CRUD) | `require_owner` |
| 12 | `overtime` | `/api/overtime` | 4 (list, get, create, calculate) | `require_owner` |
| 13 | `payroll` | `/api/payroll` | 3 (list, get, close) | `require_owner` |
| 14 | `notifications` | `/api/notifications` | 6 (list, unread, create, send, read, read-all) | `require_owner` |
| 15 | `calendar` | `/api/calendar` | 3 (get, generate, update) | `require_owner` |
| 16 | `incidents` | `/api/incidents` | 3 (list, detect, resolve) | `require_manager` |
| 17 | `settings` | `/api/settings` | 2 (get, update) | `get_current_user` / `require_owner` |
| 18 | `billing` | `/api/billing` | 4 (checkout, webhook, status, portal) | `require_owner` |
| 19 | `devices` | `/api/devices` | 1 (create) | `require_manager` |

**Total de endpoints:** ~82 endpoints documentados.

---

## Apéndice B: Autenticación por endpoint

| Nivel de auth | Endpoints |
|---------------|----------|
| **Pública** | `POST /api/auth/login`, `POST /api/auth/register`, `POST /api/auth/refresh`, `GET /api/health`, `GET /api/metrics`, `POST /api/billing/webhook` |
| **JWT (cualquier rol)** | `GET /api/auth/me`, `POST /api/auth/logout`, `GET /api/settings` |
| **`require_manager`** | Endpoints de `clock`, `incidents`, `reports`, `devices` |
| **`require_owner`** | CRUD de `employees`, `shifts`, `schedules`, `contracts`, `holidays`, `vacations`, `leave`, `overtime`, `payroll`, `notifications`, `calendar`, `settings` (PUT), `billing` |
| **`require_super_admin`** | CRUD de `tenants` |
| **Device token** | `POST /api/clock/nfc`, `POST /api/clock/qr` |

---

## Apéndice C: Rate limiting por endpoint

| Endpoint / Patrón | Límite | Ventana | Tipo |
|-------------------|--------|---------|------|
| `/api/auth/login` | 10 | 5 min (300s) | Redis-backed (IP) |
| `/api/auth/register` | 3 | 1 hora (3600s) | Redis-backed (IP) |
| `/api/clock` (POST) | 30 | 60s | Middleware (IP) |
| `/api/clock/nfc` (POST) | 30 | 60s | Middleware (IP) |
| `/api/employees` | 60 | 60s | Middleware (IP) |
| Default (resto) | 100 | 60s | Middleware (IP) |
| PIN fail (clock) | Configurable | Bloqueo N min | Redis-backed (PIN) |
| Fichaje por tenant | Configurable | 1 hora | Redis-backed (tenant) |

---

## Apéndice D: Roadmap de versionado

**Estado actual:** Todos los endpoints usan prefijo `/api/` sin versión explícita.

**Plan v1.0:** Migrar a `/api/v1/` para todos los endpoints. Esto permite:
- Mantener compatibilidad hacia atrás cuando se introduzca `/api/v2/`
- Versionado explícito en el URL
- Documentación OpenAPI versionada

**Estrategia de migración:**
1. Añadir un middleware que reescriba `/api/v1/` → `/api/` (backward compat)
2. Actualizar todos los routers para usar `prefix="/api/v1/..."`
3. Documentar la versión en OpenAPI metadata
4. Deprecar `/api/` (sin `/v1/`) con warning header

---

**Fin del documento.**  
Para la arquitectura técnica completa, ver `ARCHITECTURE.md`.  
Para el roadmap y plan de desarrollo, ver `ROADMAP.md`.  
Para la especificación de producto, ver `SPEC.md`.