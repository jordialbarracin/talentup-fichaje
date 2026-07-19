# Auditoría de Arquitectura — TalentUP Fichaje v2.0

**Fecha:** 2026-07-19
**Auditor:** Arquitecto de Software Senior
**Alcance:** Backend FastAPI + SQLAlchemy async, Frontend HTML vanilla, DB SQLite/PostgreSQL, Tests, Deploy, Seguridad, PWA, Hardware ESP32

---

## Resumen Ejecutivo

| Dimensión | Puntuación | Estado |
|---|---|---|
| **Arquitectura General** | 68/100 | Sólida base MVP, pero con deuda técnica crítica para escalar |
| **Backend (FastAPI)** | 72/100 | Bien estructurado, async correcto, pero sin Redis/colas |
| **Base de Datos** | 55/100 | Modelos completos, pero índices insuficientes y sin migraciones testeadas |
| **Seguridad** | 70/100 | Buenas prácticas generales, pero rate limiting in-memory es frágil |
| **Frontend** | 60/100 | PWA funcional, pero monolito de 3K+ líneas sin tooling |
| **Tests** | 65/100 | 49 tests, buena cobertura funcional, pero faltan tests de seguridad y estrés |
| **Deploy/DevOps** | 50/100 | Docker + GH Pages, pero sin CI para backend, sin staging |
| **Multi-tenant** | 65/100 | Aislamiento lógico correcto, pero sin particionamiento físico |

### Score Global de Arquitectura: **64/100**

---

## 1. Backend — FastAPI + SQLAlchemy Async

### Fortalezas ✅
- **Arquitectura modular**: 18 routers separados por dominio, bien organizados
- **Async correcto**: SQLAlchemy async + asyncpg para PostgreSQL, aiosqlite para dev
- **Lifespan handler**: Uso correcto del patrón lifespan de FastAPI para init/shutdown
- **Audit logging**: Sistema de auditoría en todas las operaciones CRUD críticas
- **Incident detection engine**: Motor de detección de incidencias con 12 tipos, bien diseñado
- **Payroll engine**: Cálculo de nóminas completo con horas, OT, deducciones
- **Report generation**: PDF (reportlab) y Excel (openpyxl) con streaming response
- **WebSocket NFC**: Manager thread-safe con broadcast, reconexión, heartbeat
- **Lazy import Stripe**: El sistema de billing no bloquea el arranque si falta stripe

### Debilidades Críticas 🔴

#### 🔴 R1: Sin sistema de colas/background tasks
`/api/payroll/close` ejecuta el cálculo de nóminas de forma síncrona. Para 100 restaurantes con ~50 empleados cada uno, esto puede tomar **30+ segundos** y bloquear el worker de uvicorn. Lo mismo aplica a `detect_incidents()` y exportación de reports.

**Impacto:** Timeouts HTTP, denial of service por payroll, experiencia degradada.

**Solución:** Usar `BackgroundTasks` de FastAPI para tareas ligeras, y Celery/ARQ + Redis para tareas pesadas.

#### 🔴 R2: Sin rate limiting persistente
Todos los rate limiters (`_clock_limits`, `_pin_failures`, `_register_attempts`) son **diccionarios en memoria**. Con gunicorn + múltiples workers (o múltiples instancias en Railway), cada worker tiene su propio estado. Un atacante puede rotar entre workers para evadir el rate limit.

**Impacto:** El rate limiting es ineficaz en producción con múltiples workers.

**Solución:** Migrar a Redis (o al menos SQLite compartido) para rate limiting. Usar `slowapi` o middleware personalizado con backend Redis.

#### 🔴 R3: Sin límites de conexiones a DB
```python
engine = create_async_engine(DATABASE_URL, echo=False)
```
Sin `pool_size`, `max_overflow`, ni `pool_timeout`. Con 100 restaurantes × peticiones concurrentes, SQLAlchemy puede crear cientos de conexiones y saturar PostgreSQL.

**Impacto:** Agotamiento de conexiones en PostgreSQL, `too many clients` errors.

**Solución:** Configurar pool_size=10, max_overflow=20, pool_timeout=30.

#### 🔴 R4: Sin paginación en listados
`GET /api/employees`, `GET /api/shifts`, `GET /api/notifications` devuelven **todos los registros** sin paginación. Para super_admin viendo todos los tenants, podría ser miles de registros.

**Impacto:** Consumo de memoria O(n) en el servidor, payloads enormes.

**Solución:** Añadir `limit`/`offset` con defaults sensatos (ej: 50) a todos los list endpoints.

### Debilidades Medias 🟡

- **Sin versión en API**: `/api/` sin prefijo de versión (`/api/v1/`). Dificulta evolucionar.
- **Health check superficial**: `GET /api/health` no verifica DB ni dependencias externas.
- **Sin correlation IDs**: No hay `request_id` para trazabilidad en logs.
- **Logging básico**: Usa `logging` estándar sin JSON estructurado.
- **Importaciones dentro de funciones**: Varios `from datetime import ...` dentro de funciones en vez de al inicio del módulo.

---

## 2. Base de Datos — 19 Modelos + SQLite/PostgreSQL

### Fortalezas ✅
- **Modelos completos**: Employee con 50+ campos cubriendo datos personales, laborales, fichaje, vacaciones, económicos, formación
- **Tenant model robusto**: Configuración de convenio, vacaciones, nómina, billing
- **Alembic configurado**: `env.py` correctamente adaptado para async→sync, importa todos los modelos
- **UUIDs como strings**: `String(36)` para compatibilidad SQLite, con `uuid4()` como default
- **Cascades correctos**: `ON DELETE CASCADE` en todas las FKs de tenant
- **Inmutabilidad de clock_ins**: Diseño correcto — no se editan, solo se cancelan con motivo

### Debilidades Críticas 🔴

#### 🔴 D1: SQLite NO escala a 100 restaurantes
SQLite es **single-writer**. Con 100 restaurantes × 500 empleados = 50,000 empleados, y picos de fichaje a las 8:00, 15:00 y 23:00, las escrituras concurrentes producirán `database is locked` constantemente.

**Impacto:** El sistema colapsa en producción con más de ~5 restaurantes concurrentes.

**Solución:** PostgreSQL obligatorio desde el día 1, incluso en desarrollo. Eliminar el fallback a SQLite.

#### 🔴 D2: Índices insuficientes
Solo **1 índice explícito** en los modelos SQLAlchemy (`ix_employees_pin_hash_fast`). El `schema.sql` tiene 4 índices más, pero **no se crean en SQLAlchemy**. Las queries más frecuentes:

```sql
-- Sin índice compuesto:
SELECT ... FROM clock_ins WHERE tenant_id = ? AND employee_id = ? ORDER BY timestamp DESC
SELECT ... FROM clock_ins WHERE tenant_id = ? AND timestamp >= ? AND timestamp <= ?
```

**Impacto:** Full table scans en `clock_ins` (la tabla más grande) para cada petición de histórico.

**Solución:** Añadir índices compuestos:
- `(tenant_id, employee_id, timestamp)` en clock_ins
- `(tenant_id, date)` en schedules, incidents
- `(tenant_id, employee_id, date)` en schedules
- `(tenant_id, is_active)` en employees

#### 🔴 D3: Sin migraciones de datos
Solo 1 migration (initial). Cualquier cambio de schema requiere regenerar la migration. No hay tests que verifiquen que `alembic upgrade head` + `alembic downgrade -1` funcionan.

**Impacto:** Riesgo alto en despliegues a producción. No hay rollback garantizado.

### Debilidades Medias 🟡

- **JSONB en schema.sql pero JSON en SQLAlchemy**: `old_value`/`new_value` como `sa.JSON()` en vez de `sa.dialects.postgresql.JSONB`. En PostgreSQL, JSONB es más eficiente y permite índices GIN.
- **Sin unique constraint en email de tenant**: `User.email` tiene unique, pero `Tenant.email` no.
- **Sin índices en FKs**: `tenant_id` aparece en 15+ tablas pero no tiene índice explícito en SQLAlchemy (PostgreSQL auto-indexa FKs, SQLite no).

---

## 3. Seguridad

### Fortalezas ✅
- **bcrypt para passwords**: `passlib` con bcrypt, correcto
- **PIN con doble hash**: SHA256 rápido para lookup O(1) + bcrypt como verificación autoritativa (defense in depth)
- **JWT con expiración configurable**: Default 8h, configurable vía env
- **Rate limiting en clock**: 10/min por IP+tenant, con bloqueo de PIN tras 5 fallos
- **Rate limiting en registro**: 3/hora por IP
- **CORS configurable**: Orígenes permitidos vía env var
- **Audit logging**: Todas las operaciones CRUD quedan registradas
- **Aislamiento multi-tenant**: Filtrado por `tenant_id` en todas las queries
- **Stripe webhook con verificación**: `stripe.Webhook.construct_event()` con firma
- **PIN no expuesto en API**: `to_dict()` excluye `pin_hash` explícitamente

### Debilidades Críticas 🔴

#### 🔴 S1: Stripe webhook sin verificación en dev
```python
if STRIPE_WEBHOOK_SECRET and sig_header:
    # verify
else:
    # Dev mode — parse directly without verification
    event = json.loads(payload)
```

Si alguien despliega con `STRIPE_WEBHOOK_SECRET=""` (el default), **cualquiera puede enviar webhooks falsos** y modificar planes de suscripción.

**Impacto:** Riesgo de fraude: un atacante puede enviar `checkout.session.completed` falso y activar planes premium sin pago.

**Solución:** Hacer obligatoria la verificación. Si no hay `STRIPE_WEBHOOK_SECRET`, el webhook debe devolver 503.

#### 🔴 S2: Sin Content Security Policy (CSP)
No hay headers CSP en ninguna respuesta. El frontend renderiza datos del backend sin sanitización explícita. Aunque es HTML vanilla (sin dangerouslySetInnerHTML), los nombres de empleados y otras cadenas se insertan directamente.

**Impacto:** Riesgo de XSS si un empleado introduce código malicioso en su nombre.

**Solución:** Añadir middleware CSP y sanitizar outputs en el frontend.

#### 🔴 S3: Service Worker cachea datos sensibles
```javascript
if (response.status === 200) {
    caches.open(CACHE_NAME).then(cache => {
        cache.put(request, clone);  // Cachea respuestas API con datos de empleados
    });
}
```

En un dispositivo compartido, cualquier persona puede abrir las DevTools y leer la cache de API con datos personales (nombres, DNIs, IBANs).

**Impacto:** Fuga de datos personales (RGPD/LOPDGDD).

**Solución:** No cachear respuestas API que contengan datos sensibles, o usar Cache-Control: no-store en el backend.

### Debilidades Medias 🟡

- **JWT sin refresh token**: El token dura 8h y no hay mecanismo de refresh. Si alguien obtiene el token, tiene acceso 8h.
- **Sin HTTPS enforcement**: No hay redirect HTTP→HTTPS en la app (asume reverse proxy).
- **Sin limitación de tamaño de request**: No hay middleware limitando body size. Un atacante puede enviar payloads de GB.
- **Secret Key generada aleatoriamente en dev**: Correcto para dev, pero si alguien deploya sin `JWT_SECRET`, la clave cambia en cada reinicio, invalidando todos los tokens.

---

## 4. Frontend — HTML Vanilla + PWA

### Fortalezas ✅
- **PWA completa**: manifest.json, service worker, iconos, splash, standalone mode
- **Diseño Apple HIG**: Tipografía SF Pro, safe areas, gestos nativos, animaciones fluidas
- **UX de fichaje pulido**: PIN digits individuales, auto-toggle in/out, feedback háptico visual
- **Offline banner**: Detección de conectividad con UI clara
- **SVG icons**: Sin dependencias externas, icons inline en SVG
- **Responsive**: Adaptado a móvil y desktop con media queries
- **Brand consistente**: #FF6B35 en toda la UI

### Debilidades Críticas 🔴

#### 🔴 F1: Monolito de 3185 líneas en un solo HTML
`frontend/index.html` contiene HTML + CSS + JS en un solo archivo. Sin módulos, sin build step, sin type checking, sin tests. Mantener esto a largo plazo será insostenible.

**Impacto:** Cualquier cambio requiere entender 3K+ líneas. Bugs difíciles de aislar. Sin tests de frontend.

**Solución:** Dividir en módulos JS (incluso sin build step, usando ES modules nativos con `type="module"`).

#### 🔴 F2: Sin tests de frontend
No hay tests para la UI. Ni unitarios, ni de integración, ni e2e. El `package.json` solo tiene Playwright para screenshots.

**Impacto:** Cada cambio en el frontend es un riesgo. No hay red de seguridad.

#### 🔴 F3: Sin manejo de errores consistente
El JS del frontend no tiene un sistema centralizado de errores. Los errores de API se manejan caso por caso. No hay logging de errores del lado del cliente.

**Impacto:** Errores silenciosos en producción. Difícil depurar problemas de usuarios.

### Debilidades Medias 🟡

- **Sin lazy loading**: Todo el JS se carga al inicio. Para 500 empleados, las listas pueden ser lentas.
- **Sin virtual scrolling**: Las tablas de empleados renderizan todos los rows. Con 500 empleados, el DOM tiene 500+ nodos.
- **Sin estado global**: No hay store (Redux/Zustand/etc). El estado se maneja con variables globales y DOM queries.
- **Sin a11y**: Faltan roles ARIA, focus management, y soporte de lectores de pantalla.

---

## 5. Tests — 49 Tests, 877 Líneas

### Fortalezas ✅
- **Cobertura funcional buena**: Auth, employees CRUD, clock (PIN/NFC/QR), shifts, vacations, leave, holidays, reports, security
- **Aislamiento correcto**: In-memory SQLite, drop_all después de cada test
- **Seed data completo**: 2 tenants, 3 usuarios, 2 shifts, 3 empleados, vacation, leave, holiday
- **Cross-tenant testing**: Verifica que Tenant B no ve datos de Tenant A
- **Rate limiting tests**: Verifica 429 después de exceder límites
- **PIN blocking test**: Verifica bloqueo tras 5 intentos fallidos
- **Expired token test**: Verifica 401 con token expirado
- **Incident detection tests**: 3 tests para late, no_clock_in, early_leave
- **Report export tests**: PDF y Excel con verificación de content-type

### Debilidades Críticas 🔴

#### 🔴 T1: Sin tests de seguridad ofensiva
No hay tests para:
- SQL injection en campos de texto
- XSS en nombres/descripciones
- JWT tampering (firmas inválidas, algoritmos none)
- IDOR (Insecure Direct Object Reference) más allá del básico
- Rate limiting bypass con headers falsos (X-Forwarded-For)
- Carga masiva (stress testing)

**Impacto:** Vulnerabilidades de seguridad no detectadas hasta producción.

#### 🔴 T2: Sin tests de integración con PostgreSQL
Todos los tests usan SQLite in-memory. SQLite y PostgreSQL tienen diferencias significativas:
- SQLite no tiene JSONB
- SQLite no valida FKs por defecto
- SQLite no tiene tipos nativos de timestamp con timezone
- SQLite no soporta `SELECT ... FOR UPDATE`

**Impacto:** Bugs que solo aparecen en producción con PostgreSQL.

#### 🔴 T3: Sin tests de concurrencia
No hay tests que verifiquen comportamiento bajo carga concurrente (ej: 10 empleados fichando al mismo tiempo). Las race conditions en rate limiting y clock transitions no están cubiertas.

**Impacto:** Condiciones de carrera no detectadas.

### Debilidades Medias 🟡

- **Sin tests de billing**: Stripe checkout, webhooks, portal — todo sin test.
- **Sin tests de payroll**: El cálculo de nóminas no tiene tests.
- **Sin tests de WebSocket**: El endpoint `/ws/nfc` no tiene tests.
- **Sin tests de migrations**: No se verifica que `alembic upgrade` + `downgrade` funcionen.
- **Sin tests de rendimiento**: No hay benchmarks para las queries más comunes.
- **Cobertura de código no medida**: No hay `pytest-cov` configurado.

---

## 6. Multi-tenant — Aislamiento para 500 Empleados

### Fortalezas ✅
- **Aislamiento lógico correcto**: Toda query filtra por `tenant_id`
- **Super admin con visibilidad global**: Rol especial con acceso a todos los tenants
- **Owner/manager roles**: Roles dentro del tenant con permisos graduados
- **Cascades correctos**: Eliminar un tenant elimina todos sus datos
- **Seed data multi-tenant**: Tests verifican aislamiento entre Tenant A y B

### Debilidades 🔴
- **Sin particionamiento físico**: Todos los tenants comparten las mismas tablas. Un query pesado de un tenant puede afectar a todos.
- **Sin límite de empleados por plan**: `max_employees` existe en el modelo pero no se valida en los endpoints de creación.
- **Sin cuotas de API por tenant**: No hay límite de requests por tenant, solo por IP.
- **Sin tenant_id en todas las queries**: Auditoría: `audit_log` permite `tenant_id=NULL` para acciones de super_admin, pero algunas queries de super_admin no filtran por tenant.

---

## 7. Stripe Billing

### Fortalezas ✅
- **Lazy import**: Stripe no bloquea el arranque si no está instalado
- **Webhook handlers completos**: checkout.completed, invoice.paid, subscription.deleted, subscription.updated
- **Customer portal**: Sesión de Stripe Customer Portal para autogestión
- **Metadata enlace tenant**: `tenant_id` en metadata de checkout sessions y subscriptions
- **BillingRecord**: Historial de transacciones

### Debilidades 🔴
- **Webhook sin verificación en dev** (ver S1 arriba)
- **Sin idempotency keys**: Los webhooks de Stripe pueden enviarse múltiples veces. No hay protección contra doble procesamiento.
- **Sin manejo de `invoice.payment_failed`**: No se notifica al tenant ni se degrada el plan automáticamente.
- **Sin webhook reattempt**: Si el handler falla, Stripe reintenta pero el endpoint puede devolver 500.

---

## 8. Performance — Cuellos de Botella

### Identificados

| # | Cuello de Botella | Impacto | Prioridad |
|---|---|---|---|
| 1 | **SQLite single-writer** | El sistema no escala más allá de ~5 restaurantes concurrentes | 🔴 Crítico |
| 2 | **Falta de índices en clock_ins** | Full table scans en la tabla más grande y frecuente | 🔴 Crítico |
| 3 | **Payroll síncrono** | Bloquea el worker por 30+ segundos | 🔴 Crítico |
| 4 | **Sin connection pooling configurado** | Agotamiento de conexiones PostgreSQL | 🟡 Alto |
| 5 | **Listados sin paginación** | Payloads enormes para super_admin | 🟡 Alto |
| 6 | **Rate limiting en memoria** | Ineficaz con múltiples workers | 🟡 Alto |
| 7 | **Sin caché de consultas frecuentes** | Misma query de clock se ejecuta N veces | 🟡 Medio |
| 8 | **Frontend sin virtual scrolling** | DOM hinchado con 500+ empleados | 🟡 Medio |

---

## Top 3 Riesgos

### 🥇 RIESGO #1: SQLite como base de datos compartida no escala
**Severidad:** CRÍTICO | **Probabilidad:** Alta (100 restaurantes en producción)

El sistema usa SQLite por defecto y solo cambia a PostgreSQL vía env var. SQLite es single-writer. Con 100 restaurantes haciendo fichajes simultáneos en hora punta (8:00, 15:00, 23:00), las escrituras concurrentes producirán `database is locked` constantemente. Además, el `init_db()` usa `create_all()` en SQLite, que no aplica migraciones — el schema en producción puede divergir del de desarrollo.

**Recomendación:** Hacer PostgreSQL obligatorio. Eliminar el fallback a SQLite. Usar migraciones Alembic también en desarrollo.

### 🥇 RIESGO #2: Rate limiting ineficaz en producción
**Severidad:** ALTO | **Probabilidad:** Media

Todos los rate limiters son diccionarios en memoria. Con gunicorn + múltiples workers (o múltiples instancias en Railway), cada worker tiene su propio estado. Un atacante puede rotar peticiones entre workers para evadir el límite de 10/min y hacer brute-force de PINs indefinidamente.

**Recomendación:** Migrar rate limiting a Redis. Usar `slowapi` con backend Redis.

### 🥇 RIESGO #3: Stripe webhook sin verificación en deployment accidental
**Severidad:** ALTO | **Probabilidad:** Baja pero impacto severo

Si `STRIPE_WEBHOOK_SECRET` no está configurado (string vacío por defecto), el webhook procesa eventos sin verificar la firma. Un atacante que descubra la URL del webhook puede enviar eventos falsos de `checkout.session.completed` y activar planes premium sin pagar.

**Recomendación:** Hacer obligatoria la verificación. Si no hay webhook secret, devolver 503.

---

## Top 3 Mejoras

### 🥇 MEJORA #1: Migrar a PostgreSQL + Redis + Background Tasks
**Esfuerzo:** 2-3 días | **Impacto:** Crítico

- Hacer PostgreSQL obligatorio (eliminar SQLite fallback)
- Añadir Redis para rate limiting, caché, y cola de background tasks
- Migrar payroll close, incident detection, y report generation a background tasks
- Configurar connection pooling (`pool_size=10, max_overflow=20`)

### 🥇 MEJORA #2: Tests de seguridad, integración y rendimiento
**Esfuerzo:** 3-5 días | **Impacto:** Alto

- Añadir tests de SQL injection, XSS, JWT tampering, IDOR
- Tests de integración con PostgreSQL (usando testcontainers o base dedicada)
- Tests de concurrencia (10+ requests simultáneos)
- Tests de billing (Stripe webhooks mockeados)
- Tests de payroll
- Medir cobertura con `pytest-cov` (objetivo: >80%)

### 🥇 MEJORA #3: Índices compuestos + paginación + CSP
**Esfuerzo:** 1 día | **Impacto:** Alto

- Añadir índices compuestos en clock_ins, schedules, incidents
- Paginación en todos los list endpoints
- Middleware CSP (Content Security Policy)
- No cachear datos sensibles en Service Worker
- Limitar tamaño de request body

---

## Observaciones Adicionales

### Hardware ESP32
El firmware es sólido: cola offline con SPIFFS, watchdog timer, LEDs de estado, reconexión WiFi. Bien documentado. Puntos a mejorar:
- Las credenciales WiFi están hardcodeadas en el .ino (usar platformio.ini con env vars)
- No hay HTTPS para las peticiones al backend (solo HTTP)
- No hay autenticación del dispositivo (cualquier ESP32 con el tenant_id puede enviar fichajes)

### Deploy
- **GitHub Actions** solo deploya el frontend. El backend se asume en Railway manualmente.
- **Vercel** proxy API a Railway, pero sin autenticación entre Vercel y Railway.
- **Sin staging environment**: Todos los cambios van directo a producción.
- **Sin health checks de deploy**: No hay verificación post-deploy.

### Cumplimiento RGPD/LOPDGDD
- Audit logging ✅
- Datos personales extensos (DNI, SS, IBAN, datos médicos) ⚠️
- No hay política de retención de datos implementada
- No hay endpoint de export/delete de datos de un usuario (right to be forgotten)
- Service Worker cachea datos personales en el dispositivo ⚠️

---

## Conclusión

TalentUP Fichaje es un **MVP sólido y funcional** con una arquitectura bien pensada para un producto en fase inicial. El código es limpio, los patrones async son correctos, y hay atención al detalle en seguridad (doble hash de PIN, audit logging, rate limiting).

Sin embargo, **la arquitectura actual no escala a 100 restaurantes** por tres razones fundamentales:

1. **SQLite** como base de datos por defecto (single-writer)
2. **Rate limiting en memoria** (ineficaz con múltiples workers)
3. **Operaciones síncronas pesadas** (payroll, reports)

Estos tres problemas son solucionables con inversión moderada (PostgreSQL + Redis + background tasks), pero deben abordarse **antes** de escalar a más de 5-10 restaurantes concurrentes.

**Score final: 64/100** — Un 64 que refleja un producto funcional y bien diseñado para su etapa, pero con deuda técnica crítica para el escalado prometido.
