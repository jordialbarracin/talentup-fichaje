# Re-auditoría Senior V4 — TalentUP Fichaje

**Fecha:** 2026-07-20  
**Auditor:** Arquitecto de Software Senior  
**Score anterior:** 87/100  
**Score actual:** **86/100**  
**Diferencia:** -1 punto  
**Veredicto:** **No llegamos a 88+.** Se corrigieron items clave (PIN blocks con Redis, deploy workflow en raíz), pero surgieron/ persisten defectos que impiden superar el umbral.

---

## Resumen Ejecutivo

| Dimensión | Anterior | Actual | Δ | Estado |
|---|---|---|---|---|
| Backend FastAPI | 87 | 88 | +1 | PIN blocks y rate limiting de clock ahora sí usan Redis; persisten detalles menores. |
| Base de Datos | 85 | 86 | +1 | Más listados paginados en BD, pero payroll sigue paginando en memoria. |
| Seguridad | 87 | 87 | 0 | Sin cambios significativos desde V3. |
| Tests | 88 | 88 | 0 | 64/64 pasan, siguen solo en SQLite. |
| DevOps / Deploy | 80 | **74** | **-6** | Workflow movido a raíz, pero **mal configurado** (Dockerfile no está en `backend/`). |
| Frontend / PWA | 70 | 70 | 0 | Sin cambios. |
| Multi-tenant | 72 | 72 | 0 | Sin cambios. |
| **Global** | **87** | **86** | **-1** | **No se alcanza 88+.** |

---

## 1. Verificación de los puntos solicitados

### 1.1 PIN blocks en Redis ✅ (parcialmente)

- `backend/app/rate_limiter.py:126-187` implementa `is_pin_blocked`, `record_pin_failure` y bloqueo por TTL usando Redis cuando `REDIS_URL` está configurado, con fallback a memoria.
- `backend/app/routers/clock.py:185` y `:218` consumen esas funciones, por lo que **el bloqueo de PIN tras 5 fallos ya es distribuido** en producción.
- **Pero** `clock.py:120-142` conserva stores locales `_pin_limits`, `_nfc_limits`, `_qr_limits` y una lógica híbrida redundante. No es un bloqueador, pero dificulta mantenimiento y puede desincronizar rate-limiting si Redis falla y se mezcla con memoria.

**Veredicto:** Cumple la función solicitada; código limpiable.

### 1.2 Deploy workflow en raíz ✅❌ (ubicación correcta, configuración rota)

- `.github/workflows/deploy-backend.yml` ahora vive en la **raíz del repositorio** ✅.
- **Problema grave:** el job usa `working-directory: ./backend` y `railway up`. El `Dockerfile` real está en la raíz (`./Dockerfile`), no en `backend/`. Además, el Dockerfile referencia `backend/requirements.txt` y `backend/app` con rutas relativas a la raíz.
- Consecuencia: Railway no encontrará el Dockerfile en `./backend`; el deploy probablemente falle o usará un buildpack por defecto no deseado.
- El workflow de CI `backend-ci.yml:84-85` también apunta a `./backend/Dockerfile`, que no existe.

**Veredicto:** El workflow está en raíz, pero la ruta del Dockerfile está mal. Hace más daño que beneficio hasta que se corrija.

### 1.3 Paginación completa ⚠️ (casi, pero no del todo)

Routers que usan `paginate()` de SQLAlchemy (paginación en BD):
- `employees.py`, `shifts.py`, `schedules.py` ✅, `contracts.py`, `holidays.py`, `vacations.py`, `leave.py`, `overtime.py`, `notifications.py`, `calendar.py`, `incidents.py` ✅, `tenants.py` ✅, `clock/history`, `reports/hours`, `reports/incidents`.

**Falla principal:**
- `payroll.py:23-69` carga **todos** los registros con `result.scalars().all()` y luego pagina la lista en Python. Es O(n) en BD y memoria. No es paginación de BD.

**Veredicto:** No es "paginación completa" mientras payroll cargue todo en memoria.

### 1.4 Pool de PostgreSQL ✅

- `backend/app/database.py:65-73` configura `pool_size=20`, `max_overflow=40`, `pool_timeout=30`, `pool_recycle=1800`.
- Correcto para producción.

### 1.5 Índices ✅

- 9 índices explícitos en modelos SQLAlchemy y reflejados en la migración inicial `9b16fa110308_initial.py`.
- Incluye compuestos en `clock_ins`, `incidents`, `schedules`, `overtime`, `leaves`, `vacation_requests`, y simples en `employees.pin_hash_fast`, `billing_record.tenant_id`, `device.device_token`.
- Faltan índices útiles adicionales (`payroll.tenant_id+year+month`, `clock_ins.employee_id+timestamp`) pero los críticos existen.

### 1.6 Background tasks ✅

- `backend/app/tasks.py` define `run_payroll_close`, `run_incident_detection`, `run_report_export` + helpers `schedule_*`.
- `payroll.py:107-146`, `incidents.py:74-105`, `reports.py:191-285` encolan tareas en `BackgroundTasks` y devuelven `accepted` inmediatamente.
- Son FastAPI `BackgroundTasks`, suficientes para piloto; para escala masiva requerirán Celery/ARQ/RQ.

---

## 2. Score por dimensión (0-100)

### Backend — 88/100 (+1)

**Fortalezas:**
- PIN blocks y rate limiting de clock consumen Redis a través de `rate_limiter.py`.
- Middleware de seguridad, request ID, body limit, CSP nonce, health profundo.
- Lifespan, init_db con Alembic en PG / create_all en SQLite dev.

**Debilidades:**
- `clock.py` conserva stores de fallback locales con lógica híbrida; debería depurarse.
- Sin handler específico para `IntegrityError` (devuelve 500 genérico).
- Sin API versioning.

### Base de Datos — 86/100 (+1)

**Fortalezas:**
- Pool PG, Alembic, 9 índices, cascades, UUIDs String(36) para compatibilidad.
- schedules, incidents y tenants ahora paginan en BD.

**Debilidades:**
- `payroll.py` pagina en memoria.
- Migración inicial usa `sa.JSON()` en vez de `JSONB` para audit logs en PostgreSQL.
- Faltan índices adicionales en `payroll` y `clock_ins`.

### Seguridad — 87/100 (0)

**Fortalezas:**
- bcrypt + SHA256 rápido para PIN, JWT con expiración, refresh tokens.
- CSP/HSTS/X-Frame/XCTO, escape HTML, device tokens, webhook Stripe con firma.

**Debilidades:**
- PIN de 4 dígitos sigue siendo inherentemente débil.
- CSP `style-src 'unsafe-inline'` residual.
- `max_employees` por plan no se valida al crear empleados.

### Tests — 88/100 (0)

**Fortalezas:**
- 64/64 tests pasan (~117s).
- 15 tests de seguridad ofensiva.

**Debilidades:**
- Solo SQLite in-memory.
- Sin tests de payroll, billing, concurrencia, migraciones, frontend.
- Sin medición de cobertura.

### DevOps — 74/100 (-6)

**Fortalezas:**
- Docker multi-stage, non-root, health check.
- docker-compose con PG + Redis + health checks.
- CI pytest + build/push a GHCR.

**Debilidades críticas (nuevas):**
- `deploy-backend.yml` está en raíz pero apunta a `./backend` como working directory; el Dockerfile está en raíz.
- `backend-ci.yml` usa `context: ./backend` y `file: ./backend/Dockerfile`, que no existen.
- Sin CI con PostgreSQL real.
- Sin deploy automático a staging.

### Frontend — 70/100 (0)

Sin cambios desde V3.

### Multi-tenant — 72/100 (0)

Sin cambios desde V3.

---

## 3. Top 3 riesgos

### 🥇 RIESGO #1: Deploy workflow roto (Dockerfile no encontrado)

**Archivos:** `.github/workflows/deploy-backend.yml:18-38`, `.github/workflows/backend-ci.yml:81-85`, `./Dockerfile`  
**Severidad:** ALTO | **Probabilidad:** Alta  
**Impacto:** Cualquier push a `main/master` intentará desplegar con Railway usando `./backend` como contexto, pero el Dockerfile está en la raíz. El build fallará o usará un buildpack incorrecto, bloqueando el despliegue. El CI de Docker también fallará al no encontrar `./backend/Dockerfile`.
**Recomendación:**
- Opción A: mover `Dockerfile` y `.dockerignore` a `backend/` y ajustar los `COPY`.
- Opción B: dejar el Dockerfile en raíz y cambiar el workflow a `working-directory: .` / `context: .`, `file: ./Dockerfile`.
- Esfuerzo: 0.25 días.

### 🥈 RIESGO #2: Payroll pagina en memoria

**Archivo:** `backend/app/routers/payroll.py:23-69`  
**Severidad:** ALTO | **Probabilidad:** Media  
**Impacto:** `GET /api/payroll` carga todas las nóminas del tenant en memoria antes de paginar. Con 100 empleados × 24 meses = 2.400 registros mínimos; el consumo de memoria y tiempo de respuesta crecen linealmente. En un tenant grande puede agotar memoria del worker o causar timeouts.
**Recomendación:** Reescribir `list_payroll` para usar `paginate()` de SQLAlchemy sobre la query principal, aplicar filtros `year`, `month`, `employee_id` en BD, y luego enriquecer solo la página resultante con nombres de empleado. Esfuerzo: 0.5 días.

### 🥉 RIESGO #3: Tests solo en SQLite + sin cobertura crítica

**Archivos:** `backend/tests/conftest.py`, `backend/tests/test_api.py`, `backend/tests/test_security.py`, `backend/app/tasks.py`, `backend/app/routers/billing.py`, `backend/app/routers/payroll.py`  
**Severidad:** MEDIO | **Probabilidad:** Media  
**Impacto:** SQLite y PostgreSQL divergen en JSON/JSONB, FKs estrictos, timezones y locking. No hay tests de payroll, billing/webhook Stripe, ni fichajes concurrentes. Un bug de concurrencia en clock-in (mismo empleado, dos workers) o un cálculo de nómina incorrecto pasará desapercibido a producción.
**Recomendación:**
- Añadir job de CI opcional con PostgreSQL service container.
- Tests de `POST /api/payroll/close`, `POST /api/billing/webhook` con firma mock, y 10 fichajes concurrentes con `asyncio.gather`.
- Esfuerzo: 2-3 días.

---

## 4. Verificación ejecutada

- ✅ 64/64 tests pasan (`pytest -q`, ~117s).
- ✅ `GET /api/health` devuelve `db_status: ok`, `redis_status: disabled` (modo dev local sin Redis).
- ✅ `GET /api/employees` sin token devuelve 401.
- ✅ Docker Compose incluye PostgreSQL 16 + Redis 7 + backend con health checks.
- ❌ `deploy-backend.yml` usa `working-directory: ./backend` pero el `Dockerfile` está en la raíz.
- ❌ `backend-ci.yml` referencia `./backend/Dockerfile`, que no existe.
- ❌ `payroll.py` carga todos los registros antes de paginar.

---

## 5. Conclusión

**No llegamos a 88+.** El score baja de 87 a **86/100** por un defecto de configuración de deploy introducido al mover el workflow a raíz sin ajustar las rutas del Dockerfile. Se gana un punto en backend/database por PIN Redis y más paginación, pero se pierden 6 puntos en DevOps.

**Para llegar a 88+ (1-2 días de trabajo enfocado):**
1. Corregir rutas del Dockerfile en `backend-ci.yml` y `deploy-backend.yml`.
2. Reescribir `payroll.py` para paginar en BD.
3. (Opcional pero recomendado) Añadir un job CI con PostgreSQL.

**Score final V4: 86/100.** El producto sigue siendo viable para piloto controlado, pero el deploy automático actual está roto y debe ser la primera prioridad.
