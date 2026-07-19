# Re-auditoría CTO — TalentUP Fichaje v2.0 (post-mejoras)

**Fecha:** 2026-07-19
**Auditor:** CTO Venture Studio (subagente Hermes)
**Score anterior:** 64/100
**Score actual:** 79/100
**Diferencia:** +15 puntos

---

## Resumen Ejecutivo

| Dimensión | Anterior | Actual | Δ | Estado |
|---|---|---|---|---|
| Backend FastAPI | 72 | 84 | +12 | PostgreSQL/Redis opcional, pooling, background tasks, logs JSON |
| Base de Datos | 55 | 78 | +23 | Índices compuestos añadidos, paginación en listados clave, pooling |
| Seguridad | 70 | 82 | +12 | 64 tests, 15 de seguridad, CSP ausente, body size limit, rate Redis opcional |
| Frontend/PWA | 60 | 68 | +8 | PWA refinada, SW no cachea API, aún monolito HTML sin tests |
| Tests | 65 | 85 | +20 | 64 tests pasan, cubren SQLi, JWT, XSS, IDOR, rate limit, body size |
| DevOps/Deploy | 50 | 76 | +26 | CI backend + Docker + GHCR, compose con health checks, .env.example completo |
| **Global** | **64** | **79** | **+15** | **Mejoró sustancialmente; ya no hay bloqueadores críticos del CTO, pero faltan cosas para producción real.** |

---

## 1. Bloqueadores del CTO — Evaluación post-mejoras

### Bloqueador 1: PostgreSQL + Redis + Background Tasks
**Estado:** ✅ RESUELTO (con matices)

**Evidencia de mejora:**
- `backend/app/database.py:71-79` configura `pool_size=20, max_overflow=40, pool_timeout=30, pool_recycle=1800` cuando detecta PostgreSQL.
- `backend/app/database.py:54-60` obliga a PostgreSQL en `APP_ENV=production`; en dev/test permite SQLite.
- `backend/app/tasks.py` implementa `run_payroll_close`, `run_report_export`, `run_incident_detection` y helpers `schedule_*` con `BackgroundTasks`.
- `backend/app/routers/payroll.py:108-114` ejecuta cierre de nóminas en background.
- `backend/app/rate_limiter.py` soporta Redis (async `redis.from_url`) como backend opcional; fallback a memoria si no está configurado.
- `docker-compose.yml:7-73` levanta PostgreSQL 16 + Redis 7 + backend con health checks y `depends_on` sanos.

**Matices:**
- El rate limiting sigue siendo **local por defecto**. Si no configuras `REDIS_URL`, cada worker mantiene su propio contador. Es aceptable para MVP pero no para multi-worker prod.
- Background tasks son **FastAPI `BackgroundTasks`**, no Celery/ARQ. Para cálculos de nómina de 50 empleados es suficiente; para miles, necesitarás una cola real.

### Bloqueador 2: Tests de seguridad + Frontend mejorado
**Estado:** ✅ RESUELTO (tests) / 🟡 PARCIAL (frontend)

**Evidencia de mejora:**
- `backend/tests/test_security.py` añade 15 tests: SQLi, JWT tampering/expired, XSS escape, IDOR, cross-tenant, rate limiting, Stripe webhook missing/invalid signature, auth sin token, WebSocket sin datos sensibles, body size > 1MB.
- 64/64 tests pasan (`pytest` local, 109s).
- `backend/app/main.py:88-100` añade middleware de límite de body (1 MB) → verificado con `413` real.
- `backend/app/routers/employees.py:184-199` escapa con `html.escape` campos de texto al crear empleados.
- `mobile/sw.js` ya **no cachea** `/api/`. Es network-first para API y cache-first solo para el app shell.
- `mobile/index.html` y `frontend/index.html` tienen diseño Apple HIG pulido.

**Faltas aún:**
- **No hay CSP headers** en el backend. El XSS se mitiga escapando en el servidor, pero el navegador no recibe una política de seguridad de contenido.
- **El frontend sigue siendo un monolito HTML+CSS+JS** sin build step, sin type checking, sin tests de frontend. `frontend/package.json` solo incluye Playwright para screenshots.
- `frontend/index.html` tiene ~3.300 líneas; cualquier cambio es arriesgado.

### Bloqueador 3: DevOps + CI/CD
**Estado:** ✅ RESUELTO (backend CI) / 🟡 PARCIAL (CD a producción)

**Evidencia de mejora:**
- `.github/workflows/backend-ci.yml` corre `pytest` y construye/pushea imagen Docker a GHCR en push a `master`.
- `backend/Dockerfile` es multi-stage, non-root (uid 1000), con health check y `PYTHONUNBUFFERED/DONTWRITEBYTECODE`.
- `docker-compose.yml` tiene Postgres + Redis + backend + health checks con `condition: service_healthy`.
- `backend/app/main.py:180-228` expone `/api/health` profundo (DB SELECT 1 + Redis ping + uptime). Verificado manualmente: devuelve 200 con `db_status: ok` y `redis_status: disabled` cuando no hay Redis.
- `.env.example` cubre todas las variables reales que el código lee.

**Faltas aún:**
- No hay **deploy automatizado** a staging/producción. El workflow build-and-push sube la imagen pero no la despliega.
- No hay tests de integración con PostgreSQL en CI (usar testcontainers o base de test dedicada).
- No hay CI para el frontend más allá del deploy a GitHub Pages.
- No hay backups automatizados de BD ni TLS/SSL gestionado en el repo.

---

## 2. Top 5 hallazgos críticos que quedan

### 🔴 H1: Sin headers de seguridad (CSP/HSTS/X-Frame)
**Archivo:** `backend/app/main.py`
**Impacto:** Aunque se escapan outputs, la ausencia de CSP deja la puerta abierta a XSS vía scripts inline o payloads en otros vectores.
**Recomendación:** Añadir middleware de seguridad con CSP estricto, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy.

### 🟠 H2: `frontend/index.html` monolito sin tests
**Archivo:** `frontend/index.html` (~3.342 líneas)
**Impacto:** Mantenimiento costoso, sin regresión automatizada, difícil de escalar.
**Recomendación:** Migrar a Vite + React/Vanilla modules + Playwright e2e mínimo (1-2 días). Prioridad media porque funciona, pero es deuda real.

### 🟠 H3: Stripe webhook sigue teniendo fallback a test secret
**Archivo:** `backend/app/routers/billing.py:189-193`
**Impacto:** Si `STRIPE_WEBHOOK_SECRET` no está configurado, el endpoint usa `TEST_STRIPE_WEBHOOK_SECRET` por defecto. No es crítico porque ahora exige header `stripe-signature`, pero sigue siendo un riesgo operacional.
**Recomendación:** En producción, rechazar explícitamente si `STRIPE_WEBHOOK_SECRET` no está seteado. Separar claramente dev/test.

### 🟠 H4: No hay tests con PostgreSQL real
**Archivo:** `backend/tests/conftest.py` (usa SQLite in-memory)
**Impacto:** Diferencias de dialecto pueden romper en prod (JSON vs JSONB, FKs, timezones).
**Recomendación:** Añadir job de CI opcional con PostgreSQL 16 service container.

### 🟠 H5: Notificaciones y algunos listados aún sin paginación
**Archivo:** `backend/app/routers/notifications.py:34-52`
`backend/app/routers/reports.py` (reportes no paginados)
**Impacto:** `/api/notifications` devuelve todos los registros. Para tenants con mucha actividad, payload grande.
**Recomendación:** Aplicar helper `paginate` también en notificaciones y considerar paginación/exports async para reportes masivos.

---

## 3. Score por dimensión (explicación)

| Dimensión | Score | Razón |
|---|---|---|
| Backend | 84 | Mejoras reales: lifespan, middleware body size, logs JSON, request_id, deep health, background tasks. Penaliza: rate limiter local por defecto, sin headers de seguridad. |
| BD | 78 | Pooling configurado, índices añadidos (clock_ins, incidents, schedules), paginación en listados principales. Penaliza: SQLite permitido en dev, faltan más índices en modelos (schedules por employee_id, employees tenant+active). |
| Seguridad | 82 | 15 tests de seguridad pasan, body size limit, escape HTML, SW no cachea API, webhook requiere firma. Penaliza: ausencia de CSP/HSTS, JWT sin refresh, PIN hash salt default en dev. |
| Frontend | 68 | PWA bien pulida, UX fichaje buena, offline banner. Penaliza: monolito, sin tests, sin lazy/virtual scroll, almacena tenantId en localStorage. |
| Tests | 85 | 64 tests, buena cobertura funcional + seguridad. Penaliza: solo SQLite, sin tests de concurrencia, sin tests de billing/payroll reales, sin frontend tests. |
| DevOps | 76 | CI backend + Docker + GHCR, compose stack, health check profundo. Penaliza: sin deploy automático a prod, sin CI con PostgreSQL, sin backups/TLS. |
| **Global** | **79** | Promedio ponderado con pesos iguales. Producto ya no tiene bloqueadores CTO, pero aún no es enterprise-ready. |

---

## 4. Comparativa vs score anterior 64/100

- **Sí mejoró:** +15 puntos. Las 3 áreas bloqueadoras han sido atacadas y ya no impiden un despliegue controlado.
- **Riesgo residual principal:** ausencia de CSP y monolito frontend.
- **Próximo salto:** resolver CSP + dividir frontend en módulos + CI con PostgreSQL podría llevar el score a ~86.

---

## 5. Recomendaciones priorizadas (top 5)

1. **Añadir middleware de headers de seguridad** (CSP, HSTS, etc.) — 0.5 días, impacto alto.
2. **Forzar rate limiting Redis en producción** y no permitir fallback a memoria cuando `APP_ENV=production` — 1 día.
3. **Migrar frontend a módulos ES + añadir tests Playwright mínimos** — 2-3 días.
4. **CI con PostgreSQL** y tests de integración — 1-2 días.
5. **Pipeline de deploy** (staging + producción con validación post-deploy) — 2-3 días.

---

## Conclusión

TalentUP Fichaje ha dado un salto cualitativo importante. Pasó de un MVP con deuda técnica crítica (SQLite por defecto, rate limit en memoria, operaciones síncronas, sin CI backend) a una arquitectura razonablemente preparada para escalar: PostgreSQL obligatorio en prod, Redis opcional, background tasks, tests de seguridad, CI/CD de backend y health check profundo.

**Veredicto CTO:** Ya no hay bloqueadores para un despliegue piloto controlado. Para escalar a 100 restaurantes, resolver CSP, rate limiting Redis obligatorio, y mejorar el frontend son los siguientes pasos obligatorios.

**Score actualizado: 79/100.**
