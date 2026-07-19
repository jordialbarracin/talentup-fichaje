# Evaluación Técnica — TalentUP Fichaje
**Rol:** CTO Venture Studio | **Fecha:** 2026-07-19 | **Alcance:** Full-stack audit para inversión Serie Pre-Seed/Seed

---

## 1. Score Técnico Global: 62 / 100

| Dimensión | Peso | Score | Nota clave |
|---|---|---|---|
| **Backend (FastAPI)** | 20% | 72 | Async + SQLAlchemy 2.0 correctos; sin colas ni connection pooling |
| **Base de Datos** | 15% | 50 | Modelos completos (19 tablas), pero 1 índice explícito y SQLite fallback peligroso |
| **Seguridad** | 15% | 62 | bcrypt/JWT bien; rate limiting in-memory ineficaz en producción; CSP ausente |
| **Frontend** | 10% | 52 | PWA funcional pero monolito de 3.185 líneas sin tests ni build step |
| **Tests** | 10% | 58 | 49 tests funcionales; cero tests de seguridad ofensiva, integración PostgreSQL o estrés |
| **DevOps / Deploy** | 10% | 42 | Docker OK; CI solo frontend (GitHub Pages); sin staging, sin health checks profundos |
| **Multi-tenant** | 10% | 64 | Aislamiento lógico OK; sin particionamiento físico ni límites de empleados |
| **Producto / Negocio** | 10% | 70 | MVP funcional, cumple RD-ley 8/2019, pricing claro, hardware ESP32 |

> **Veredicto:** MVP sólido para 5-10 restaurantes piloto. **No escala a 1.000 restaurantes** con la arquitectura actual sin inversión técnica significativa (2-4 semanas de backend senior + DevOps).

---

## 2. Arquitectura: ¿Sólida?

**SÍ, como MVP. NO, como plataforma de inversión.**

- ✅ **FastAPI + SQLAlchemy async** bien implementado; 18 routers separados por dominio.
- ✅ **Lifespan handler**, audit logging, motor de incidencias, generación PDF/Excel.
- ❌ **Sin sistema de colas**: `POST /api/payroll/close` es síncrono. Para 50 empleados/restaurante × 1.000 restaurantes = bloqueo de workers de 30-120s.
- ❌ **Sin connection pooling**: `create_async_engine(DATABASE_URL, echo=False)` sin `pool_size`, `max_overflow` ni `pool_timeout`.
- ❌ **Sin paginación**: `GET /api/employees`, `GET /api/shifts`, `GET /api/clock/history` devuelven **todos** los registros. Con 500 empleados/tenant y super_admin viendo todos → payloads de MBs.
- ❌ **Sin versionado de API**: `/api/` sin `/v1/`. Imposible evolucionar sin breaking changes.

---

## 3. Escalabilidad a 1.000 Restaurantes

**Riesgo CRÍTICO. No es viable hoy.**

### Bloqueadores para escalar:
1. **SQLite single-writer**: El `main.py` hace default a SQLite (`os.environ.setdefault("DATABASE_URL", "sqlite+...")`). SQLite es single-writer; con picos de fichaje a las 8:00, 15:00 y 23:00 → `database is locked` masivo. **PostgreSQL obligatorio desde el minuto 1.**
2. **Índices insuficientes**: Solo 1 índice explícito en SQLAlchemy (`ix_employees_pin_hash_fast`). Las queries de `clock_ins` por `tenant_id + employee_id + timestamp` hacen full table scan en la tabla más grande.
3. **Rate limiting in-memory**: `_clock_limits`, `_pin_failures` son diccionarios Python. Con gunicorn + múltiples workers (Railway) o múltiples instancias, cada worker tiene su propio estado. **Un atacante puede rotar entre workers** y hacer fuerza bruta de PINs 4 dígitos.
4. **Payroll síncrono**: Calcula nóminas en el hilo de request. Timeout garantizado con escala.
5. **Sin Redis / caché**: Cada request de historial ejecuta la misma query contra PostgreSQL.

**Estimación:** Para 1.000 restaurantes concurrentes se necesita:
- PostgreSQL con connection pooling (`pool_size=20`, `max_overflow=40`)
- Redis para rate limiting distribuido + caché de sessions + colas
- Celery/ARQ para payroll, reports e incident detection en background
- Índices compuestos en `clock_ins`, `schedules`, `incidents`
- Paginación en **todos** los list endpoints
- Revisión de queries N+1 (reportes actuales hacen múltiples queries por empleado)

**Esfuerzo estimado:** 3-4 semanas de un backend senior + 1 semana DevOps.

---

## 4. Deuda Técnica

| Deuda | Severidad | Esfuerzo |
|---|---|---|
| Frontend monolito (3.185 líneas HTML+CSS+JS) | 🔴 Alta | 4-6 semanas (migrar a Vue/React modular) |
| Sin tests de frontend | 🔴 Alta | 2-3 semanas |
| SQLite fallback en producción | 🔴 Crítica | 2 días |
| Rate limiting in-memory | 🔴 Crítica | 3-5 días (Redis + slowapi) |
| Sin paginación en endpoints | 🔴 Alta | 3-4 días |
| Sin colas/background tasks | 🔴 Alta | 5-7 días |
| 1 sola migración Alembic | 🟡 Media | 1 día |
| Sin CSP / headers seguridad | 🟡 Media | 1-2 días |
| Service Worker cachea datos sensibles | 🟡 Media | 1-2 días |
| Sin CI/CD para backend | 🟡 Media | 2-3 días |
| Sin health check de DB | 🟡 Media | 1 día |
| Logging básico (sin JSON estructurado) | 🟢 Baja | 2 días |

---

## 5. Seguridad

**Puntuación: 62/100**

### Fortalezas:
- bcrypt para passwords + doble hash de PIN (SHA256 indexado + bcrypt)
- JWT con expiración configurable (8h)
- CORS configurable vía env var
- Aislamiento multi-tenant por `tenant_id` en todas las queries
- Audit logging en operaciones CRUD
- PIN no expuesto en API (`to_dict()` excluye `pin_hash`)

### Debilidades críticas:
- **Rate limiting in-memory**: Ineficaz con múltiples workers. Un atacante distribuido puede evadirlo.
- **Stripe webhook sin verificación obligatoria**: `STRIPE_WEBHOOK_SECRET` default vacío. Si se despliega sin configurar, cualquiera puede enviar webhooks falsos y activar planes premium sin pagar.
- **Sin CSP**: No hay Content Security Policy. Riesgo XSS si un empleado mete JS en su nombre.
- **Service Worker cachea respuestas API**: Datos personales (DNI, IBAN) quedan en caché del dispositivo. Violación RGPD/LOPDGDD en tablet compartida.
- **PIN en localStorage (PWA móvil)**: Persiste entre sesiones. Dispositivo robado/compartido = fichaje no autorizado.
- **Sin refresh tokens**: JWT de 8h sin mecanismo de renovación.
- **Sin limitación de body size**: Un atacante puede enviar payloads de GB.

---

## 6. SQLite → PostgreSQL: Migración

La migración **no es suficiente sola**. Es necesaria pero no suficiente:

1. **PostgreSQL obligatorio**: Eliminar el fallback a SQLite. El `main.py` hace `os.environ.setdefault("DATABASE_URL", "sqlite...")` — esto es una trampa en producción.
2. **Alembic**: Solo existe 1 migración (`initial`). En producción real se necesitan migraciones incrementales + tests de `upgrade/downgrade`.
3. **JSON vs JSONB**: `audit_log.old_value/new_value` usan `sa.JSON()` en vez de `sa.dialects.postgresql.JSONB`. En PostgreSQL, JSONB es más eficiente e indexable con GIN.
4. **Diferencias dialecto**: Los tests usan SQLite in-memory. Hay diferencias reales (tipos timestamp, FK validation, `FOR UPDATE`) que solo explotan en PostgreSQL.

**Recomendación:** Migrar tests a PostgreSQL (testcontainers o base dedicada de test) y eliminar SQLite del stack de CI.

---

## 7. Mantenibilidad

- **Backend:** Bien. 18 routers, ~7.784 líneas de Python, separación clara models/routers. Fácil de navegar para un equipo Python.
- **Frontend:** Muy mal. 3.185 líneas en un solo `index.html` + 904 líneas en `mobile/index.html` + 2.151 en `terminal/index.html`. Sin módulos JS, sin build, sin TypeScript, sin tests. Un cambio de UI requiere entender 3K+ líneas de HTML+CSS+JS mezclado.
- **Hardware:** ESP32 firmware (~20K líneas .ino) está bien documentado. Cola offline con LittleFS, watchdog timer, LEDs de estado. Pero credenciales WiFi hardcodeadas y sin HTTPS en el firmware.
- **Documentación:** Bien documentado (README, SPEC, PRIVACY, ARCHITECTURE_AUDIT). El equipo demuestra capacidad de auto-auditoría.

---

## 8. ¿Producto Listo para Vender?

**Sí, para un pilot de 5-10 restaurantes. No para venta masiva sin arreglar bloqueadores.**

- ✅ Cumple RD-ley 8/2019 (registro de jornada)
- ✅ Multi-tenant funcional con roles (super_admin, owner, manager, employee)
- ✅ Terminal físico (ESP32 + PN532 NFC) con cola offline
- ✅ PWA móvil para fichaje desde smartphone
- ✅ Stripe Checkout + Customer Portal + webhook handlers
- ✅ Exportación PDF/Excel para inspección
- ✅ Pricing claro: 29-39€/mes + 49€ kit

- ❌ Sin SLA técnico garantizable a 1.000 clientes
- ❌ Sin soporte escalable de onboarding (cada tenant requiere setup manual)
- ❌ Sin panel de administración para operaciones (backoffice interno)

---

## 9. Equipo Necesario para Escalar

| Rol | Prioridad | Esfuerzo inicial |
|---|---|---|
| **Backend Senior (Python/FastAPI/PostgreSQL)** | 🔴 Crítico | 100% durante 6-8 semanas |
| **DevOps / SRE** | 🔴 Crítico | 50% durante 4 semanas (CI/CD, monitoring, infra) |
| **Frontend Developer** | 🟡 Alta | 100% durante 6-8 semanas (modularizar PWA) |
| **QA / Seguridad** | 🟡 Alta | 50% durante 4 semanas (tests de seguridad, integración) |
| **Soporte Técnico / Onboarding** | 🟢 Media | Tiempo parcial desde el mes 1 |

**Total:** Mínimo 2 FTE técnicos senior durante 2 meses para estar listos para 1.000 restaurantes.

---

## 10. Costes de Producción (Railway + PostgreSQL + Redis)

Estimación para escala real (1.000 restaurantes activos, ~50 empleados/tenant):

| Servicio | Tier estimado | Coste mensual |
|---|---|---|
| **Railway** (backend) | 2-4 instancias Pro ($29/inst) + egress | ~$150-250/mes |
| **Neon PostgreSQL** | 50-100GB, múltiples conexiones | ~$200-400/mes |
| **Redis** (Upstash / Railway) | Pro tier, rate limiting + colas + caché | ~$30-80/mes |
| **Vercel** (frontend estático) | Hobby/Pro | ~$0-20/mes |
| **Stripe** | Fees de procesamiento (2.9% + 0.30€) | Variable (~$900/mes a 1.000×29€) |
| **Monitoring** (Sentry, Datadog, etc.) | | ~$50-100/mes |
| **Total infraestructura** (sin Stripe fees) | | **~$430-750/mes** |

> Nota: A 1.000 restaurantes × 29€/mes = 29.000€ MRR. Los costes de infraestructura (~500€/mes) son irrelevantes frente al revenue. El problema no es el coste, es la **arquitectura**.

---

## 11. Ventaja Competitiva vs Factorial / Sesame

| Factor | TalentUP | Factorial / Sesame |
|---|---|---|
| **Pricing** | 29-39€/mes por establecimiento (ilimitado empleados) | Por empleado (~4-8€/mes). Para 50 empleados = 200-400€/mes |
| **Hardware propio** | Sí: ESP32 + tablet + NFC (49€ kit) | No / integraciones de terceros |
| **Específico hostelería** | Convenio hostelería, turnos partidos, tolerancia fichaje | Genérico HR |
| **Offline-first** | Cola offline ESP32 + PWA | Requiere conexión constante |
| **Kiosk mode** | Tablet en pared, PIN grande, sin salir | No diseñado para kiosk |
| **Feature set** | Fichaje + nóminas + incidencias + informes | RRHH completo (nóminas reales, evaluaciones, ATS) |
| **Escalabilidad técnica** | MVP, sin garantías de escala | Infra empresarial probada |

**Veredicto:** TalentUP tiene un nicho claro (hostelería española, precio por establecimiento, hardware propio). Factorial/Sesame son superiores en HR general pero más caros por empleado y sin foco en kiosk/offline. **La ventaja es de producto/negocio, no de tecnología.**

---

## 12. ¿Invertiría?

**SÍ, PERO CON 3 CONDICIONES INNEGOCIABLES.**

No invertiría tal cual el proyecto está hoy (score 62). El producto es funcional y el equipo demuestra capacidad de ejecución, pero la arquitectura tiene bloqueadores críticos para escalar. Sin embargo, el nicho (hostelería española) y el modelo de precios (por establecimiento) son atractivos.

### Condición 1: PostgreSQL + Redis + Background Tasks (antes de cliente #11)
- Eliminar SQLite del stack de producción y CI.
- Añadir Redis para rate limiting distribuido, caché de sesiones y colas.
- Migrar payroll, report generation e incident detection a Celery/ARQ.
- Configurar connection pooling y añadir índices compuestos en `clock_ins`.

### Condición 2: Tests de Seguridad + Integración + Frontend Modular (antes de facturar >50K€ ARR)
- Añadir tests de SQL injection, XSS, JWT tampering, IDOR y concurrencia.
- Migrar tests de SQLite a PostgreSQL (testcontainers).
- Modularizar el frontend: separar HTML/CSS/JS en componentes (al menos ES modules nativos; idealmente React/Vue + build step).
- Añadir tests E2E con Playwright.

### Condición 3: Contratar Backend Senior + DevOps (antes de escalar a >50 restaurantes)
- El equipo actual demuestra buen product sense, pero necesita refuerzo técnico senior para infraestructura distribuida.
- Presupuestar 2 FTE técnicos senior durante 2 meses como parte del use of funds.
- Establecer CI/CD completo (backend + frontend), entorno de staging y health checks profundos.

---

## Resumen para el Comité de Inversión

- **Producto:** 7/10 — MVP funcional, nicho claro, pricing competitivo.
- **Tecnología:** 6/10 — Buena base, deuda técnica crítica para escala.
- **Equipo:** Capacidad de ejecución demostrada (auditorías propias, iteración rápida), pero falta experiencia en sistemas distribuidos.
- **Riesgo principal:** Técnico (escalabilidad). No de mercado.
- **Recomendación:** **Invertir con reserva técnica** — asignar un tramo del funding condicionado a cumplir las 3 condiciones técnicas en los primeros 90 días post-inversión.
