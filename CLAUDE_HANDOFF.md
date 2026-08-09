# CLAUDE HANDOFF — TalentUP Fichaje

> **Para:** Claude Opus
> **Trigger:** Cron a las 22:00 (08 Aug 2026)
> **Repositorio:** `C:\Users\jordi\talentup-fichaje` · git `origin` → `github.com/jordialbarracin/talentup-fichaje`
> **Rama:** `master` (up to date con origin; hay cambios sin commitear y archivos untracked)
> **Generado por:** Hermes Agent (subagente), 08 Aug 2026 ~21:05

---

## 0. CONTEXTO EJECUTIVO

TalentUP Fichaje es un SaaS de fichaje digital para hostelería (FastAPI + SPA vanilla JS + ESP32 NFC). El proyecto está en v1.0.0-en-desarrollo. El backend tiene 19 routers, 23 modelos, 64 tests, multi-tenant con JWT. Hay un design system nuevo (`design_system.css` + `STYLE_GUIDE.md` + `COMPONENT_GUIDE.md`) y un esqueleto HTML nuevo del dashboard (`dashboard_structure.html`) que **no tiene estilos propios** — solo estructura + clases del design system. El comentario en línea 18 de ese archivo dice explícitamente: *"Claude Opus estilizara a las 22:00 sobre esta base."*

**Tu trabajo principal a las 22:00:** generar el dashboard estilizado y production-ready a partir de `dashboard_structure.html` + `design_system.css`, y commitear/deployar el resultado.

---

## 1. ESTADO DEL REPOSITORIO (git status real)

### Commits recientes (master)
```
a73ecd0 feat: simulate_nfc_flow.py, firmware tests, backend improvements from agents
d16a91a feat: terminos.html, contacto.html, firmware tests, DB optimizations from agents
565c3b3 wip: 30 agentes corriendo, libro 1 6.6K palabras, PWA, OpenAPI, landing deployado
cf20cfa fix: clock/today timezone bug, 121/121 tests passing
78d64c4 feat: OpenAPI/Swagger documentation with response models, tags, examples
f096ec9 feat: JWT refresh tokens, rate limiting, DPA, Grafana, CI/CD, i18n, README update
```

### Cambios sin commitear (modified)
- `frontend/contacto.html`
- `frontend/icon-192.svg`, `frontend/icon-512.svg`
- `frontend/landing.html`
- `frontend/terminos.html`
- `frontend/vercel.json`
- `landing.html` (raíz — symlink/duplicado del frontend)

### Archivos untracked (NO commiteados aún)
**Frontend v2 — el nuevo design system y dashboard:**
- `frontend/design_system.css` ← **fuente de verdad de tokens (894 líneas)**
- `frontend/dashboard_structure.html` ← **esqueleto a estilizar (915 líneas)**
- `frontend/dashboard_new.html` ← versión intermedia con JS demo (1448 líneas, untracked)
- `frontend/landing_new.html` ← landing nueva (49KB)
- `frontend/STYLE_GUIDE.md`, `frontend/COMPONENT_GUIDE.md` ← docs del design system
- `frontend/sw_v2.js` ← service worker v2
- `frontend/manifest_v2.json` ← manifest PWA v2
- `frontend/apple-touch-icon.svg`, `icon-16.svg`, `icon-32.svg`, `icon-maskable.svg`
- `frontend/screenshot-desktop-dashboard.svg`, `screenshot-mobile-dashboard.svg`
- `frontend/shortcut-dashboard.svg`, `shortcut-empleados.svg`, `shortcut-fichajes.svg`, `shortcut-incidencias.svg`
- `frontend/_audit_landing.mjs`, `frontend/_shot.mjs` ← scripts de auditoría/screenshot

**Otros:**
- `docs/email_ventas.md`, `docs/onboarding.md`
- `public/robots.txt`, `public/sitemap.xml`

---

## 2. ARQUITECTURA — QUE ARCHIVOS EXISTEN

### Backend (`backend/app/`)
```
main.py              — app FastAPI, lifespan, middleware (CSP nonce, rate limit, body limit)
auth.py              — JWT access+refresh, bcrypt, PIN hash (SHA256+bcrypt)
database.py          — async engine, pool PG (20/40/30), init_db (Alembic en PG, create_all en SQLite)
rate_limiter.py      — sliding window per IP+endpoint, PIN blocks con Redis + fallback memoria
rate_limit.py        — decorator de rate limiting
tasks.py             — BackgroundTasks: payroll close, incident detection, report export
seed.py              — datos de ejemplo
pagination.py        — helper paginate() SQLAlchemy
rls.py               — row-level security helpers
audit.py             — audit log
metrics.py           — Prometheus
logging_config.py    — JSON logging
openapi_docs.py      — 718 líneas, OpenAPI/Swagger con response models y tags
migrate_pin_hash_fast.py

routers/ (19): auth, billing, calendar, clock, contracts, devices, employees,
              holidays, incidents, leave, notifications, overtime, payroll,
              reports, schedules, settings, shifts, tenants, vacations

models/ (23): audit_log, billing_record, clock_in, contract, device,
              document_template, employee, geofence, holiday, incident,
              leave, notification, overtime, payroll, schedule, shift,
              tenant, user, vacation, vacation_request, work_calendar
```

### Frontend (`frontend/`)
```
index.html           — SPA ACTUAL en producción (1234 líneas, inline <style>, tracked en git)
src/app.js           — lógica SPA (3114 líneas)
i18n.js              — ES/CA/EN (177 strings)
sw.js                — service worker v1 (tracked)
manifest.json       — manifest v1 (tracked)
landing.html         — landing en producción (tracked)
terminos.html        — Términos de Servicio (modified)
contacto.html        — Contacto (modified)
offline.html         — fallback offline

--- NUEVO (v2, untracked) ---
design_system.css    — design tokens completos (894 líneas)
dashboard_structure.html — esqueleto del dashboard a estilizar (915 líneas)
dashboard_new.html   — versión intermedia con JS demo (1448 líneas)
landing_new.html     — landing rediseñada
STYLE_GUIDE.md       — guía de estilo (referencia a design_system.css)
COMPONENT_GUIDE.md   — catálogo de componentes UI (28KB)
sw_v2.js             — service worker v2
manifest_v2.json     — manifest PWA v2
icon-*.svg            — iconos nuevos (16,32,192,512,maskable,apple-touch)
shortcut-*.svg       — shortcuts PWA (dashboard, empleados, fichajes, incidencias)
screenshot-*.svg     — screenshots PWA (desktop, mobile)
```

### Hardware (`hardware/`)
```
esp32_fichaje/       — firmware ESP32 SPI (363 líneas)
esp32_fichaje_cyd/   — firmware CYD 2432S028 + PN532 I2C + OTA + WDT + offline queue (911 líneas)
```

### Docs (`docs/`)
```
CASO_PRACTICO.md, GUIA_TECNICA.md, MANUAL_USUARIO.md, email_ventas.md, onboarding.md
```

### CI/CD (`.github/workflows/`)
```
ci.yml               — pytest + coverage + firmware build (PlatformIO)
```
⚠️ Existen referencias en auditorías a `deploy-backend.yml` y `backend-ci.yml` que apuntan a `./backend/Dockerfile` — **pero el Dockerfile real está en `backend/Dockerfile`** (verificado: existe). Revisar coherencia.

---

## 3. QUE FALTA / ESTÁ INCOMPLETO

### 🔴 CRÍTICO — Tarea principal del cron 22:00

1. **Dashboard sin estilizar.** `dashboard_structure.html` (915 líneas) tiene la estructura HTML completa (sidebar, 7 páginas: dashboard, empleados, fichajes, turnos, reportes, incidencias, ajustes) con clases del design system, pero **no tiene `<style>` propio**. Solo carga `design_system.css`. Necesita estilos de layout, composición de páginas, estados visuales, responsive, y microinteracciones. Este es el esqueleto que debes estilizar.

2. **Dashboard no commiteado.** `dashboard_structure.html`, `design_system.css` y todo el frontend v2 son untracked. Después de estilizar, hay que commitear y eventualmente deployar.

### 🟡 IMPORTANTE — Fixes pendientes de auditorías

3. **`payroll.py` pagina en memoria** (`backend/app/routers/payroll.py:23-69`). Carga `result.scalars().all()` y luego pagina en Python. Debe usar `paginate()` de SQLAlchemy sobre la query principal con filtros `year`/`month`/`employee_id` en BD. (Auditoría V4, riesgo #2.)

4. **Deploy workflow Dockerfile path.** Las auditorías (V4) reportan que `.github/workflows/deploy-backend.yml` y `backend-ci.yml` apuntan a `./backend/Dockerfile` o usan `context: ./backend`. Verificar si `backend/Dockerfile` existe (sí existe según `ls backend/`). Confirmar que los paths del workflow coinciden. (Auditoría V4, riesgo #1.)

5. **`clock.py` stores de fallback locales redundantes** (`backend/app/routers/clock.py:120-142`). Conserva `_pin_limits`, `_nfc_limits`, `_qr_limits` locales además del `rate_limiter.py` con Redis. Lógica híbrida que puede desincronizar. Limpiar y delegar todo a `rate_limiter.py`.

6. **Tests solo en SQLite.** Sin tests de payroll, billing, concurrencia, migraciones, frontend. Sin medición de cobertura en CI (aunque `ci.yml` tiene step de coverage, no hay tests de los routers nuevos).

### 🟢 MENOR — Mejoras

7. **Migración inicial usa `sa.JSON()` en vez de `JSONB`** para audit logs en PostgreSQL.
8. **Faltan índices** en `payroll.tenant_id+year+month` y `clock_ins.employee_id+timestamp`.
9. **`max_employees` por plan no se valida** al crear empleados (`billing.py`).
10. **CSP `style-src 'unsafe-inline'`** residual (necesario para frontend vanilla).
11. **OpenAPI expuesto** en `/docs` y `/openapi.json` — considerar proteger en producción.
12. **Stripe webhook devuelve 503** si no hay Stripe configurado (debería ser 403 fail-closed).

---

## 4. TAREAS PRECISAS PARA CLAUDE OPUS A LAS 22:00

### TAREA 1 — Estilizar el dashboard [PRINCIPAL]

**Objetivo:** Generar un dashboard production-ready estilizado a partir del esqueleto.

**Archivos de entrada:**
- `frontend/dashboard_structure.html` — esqueleto (915 líneas, 7 páginas)
- `frontend/design_system.css` — tokens (894 líneas, fuente de verdad)
- `frontend/STYLE_GUIDE.md` — principios y paleta
- `frontend/COMPONENT_GUIDE.md` — catálogo de componentes
- `frontend/index.html` — referencia del dashboard actual (para ids, data-page, data-i18n que `src/app.js` espera)

**Reglas estrictas (de STYLE_GUIDE.md):**
1. El naranja (`--brand: #FF6B35`) es **acento, nunca fondo de superficie grande**. Tintes al 6–12%.
2. Targets táctiles ≥ 44px en app, ≥ 60px en kiosco.
3. **Sin gradientes decorativos, sin sombras dramáticas.** Una sola familia de sombras (alpha ≤ 0.08).
4. Una sola acción primaria por pantalla.
5. **No hay modo oscuro** (decisión de producto). Si el navegador fuerza uno, mantener superficie clara.
6. Todo valor vivo como `var(--token)`. No hardcodear colores, radios ni espacios.

**Páginas a estilizar (data-page en dashboard_structure.html):**
| Página | id | Líneas aprox. |
|---|---|---|
| Dashboard (resumen) | `page-dashboard` | 126–291 |
| Empleados | `page-empleados` | 293–409 |
| Fichajes | `page-fichajes` | 411–525 |
| Turnos | `page-turnos` | 527–601 |
| Reportes | `page-reportes` | 603–716 |
| Incidencias | `page-incidencias` | 718–786 |
| Ajustes | `page-ajustes` | 788–913 |

**Qué añadir:**
- Bloque `<style>` en `dashboard_structure.html` (o stylesheet separado `dashboard.css`) con:
  - Layout del shell: sidebar (fixed, `--sidebar-w`), navbar (sticky, blur), main content
  - Responsive: sidebar colapsable en móvil (hamburger), grids que pasen a 1 columna
  - Estados visuales: hover, active, focus-visible, disabled, loading (skeletons)
  - Composición de cada página: stats-grid, table-card, week-calendar, tabs, switch-rows
  - Microinteracciones sutiles (transiciones `--dur-base` con `--ease-out`)
  - Print styles para reportes (cumplimiento legal RD-ley 8/2019)
- Verificar que los `data-page` e `id="page-*"` coinciden con los que `src/app.js` espera (ver `app.js:227`: `page-content[id^="page-"]`). Los nombres de página en `dashboard_structure.html` son: `dashboard, empleados, fichajes, turnos, reportes, incidencias, ajustes`. Los de `index.html` son: `dashboard, empleados, calendario, turnos, fichajes, vacaciones, bajas, informes, configuracion`. **No coinciden.** Decidir: ¿adaptar `dashboard_structure.html` a los nombres de `index.html` (para que `app.js` funcione sin cambios), o adaptar `app.js`? Recomendación: alinear `dashboard_structure.html` a los ids que `app.js` ya usa, o crear un mapeo.

**Verificación:**
- Abrir `dashboard_structure.html` en navegador (servir con `python -m http.server 3000` desde `frontend/`).
- Verificar que las 7 páginas se ven correctamente, que el sidebar navega, que es responsive.
- Si hay scripts de screenshot (`_shot.mjs`, `screenshot-dashboard.mjs`), usarlos para capturar evidencia.

### TAREA 2 — Commitear el frontend v2

Después de estilizar:
```bash
cd /c/Users/jordi/talentup-fichaje
git add frontend/design_system.css frontend/dashboard_structure.html frontend/STYLE_GUIDE.md frontend/COMPONENT_GUIDE.md
git add frontend/sw_v2.js frontend/manifest_v2.json frontend/landing_new.html
git add frontend/icon-*.svg frontend/shortcut-*.svg frontend/screenshot-*.svg frontend/apple-touch-icon.svg
git add frontend/vercel.json frontend/contacto.html frontend/terminos.html frontend/landing.html
git add landing.html docs/ public/ robots.txt sitemap.xml
git commit -m "feat: design system v2 + dashboard estilizado + PWA v2"
```

Decidir qué hacer con `dashboard_new.html` (versión intermedia con JS demo) — probablemente no commitear o marcar como referencia.

### TAREA 3 — Fix: payroll paginación en BD [si hay tiempo]

**Archivo:** `backend/app/routers/payroll.py:23-69`

**Actual (roto):**
```python
result = await db.execute(select(Payroll).where(...))
all_records = result.scalars().all()  # ← carga TODO en memoria
# luego pagina en Python con slice
```

**Objetivo:**
```python
query = select(Payroll).where(Payroll.tenant_id == tenant_id)
if year: query = query.where(Payroll.year == year)
if month: query = query.where(Payroll.month == month)
if employee_id: query = query.where(Payroll.employee_id == employee_id)
query = query.order_by(Payroll.year.desc(), Payroll.month.desc())
items, total, pages = await paginate(db, query, page, per_page)
# enriquecer solo la página con nombres de empleado
```

Usar el helper `paginate()` de `backend/app/pagination.py`.

### TAREA 4 — Fix: limpiar clock.py rate limiter híbrido [si hay tiempo]

**Archivo:** `backend/app/routers/clock.py:120-142`

Eliminar los stores locales `_pin_limits`, `_nfc_limits`, `_qr_limits` y la lógica híbrida redundante. Delegar todo a `backend/app/rate_limiter.py` (que ya tiene Redis + fallback memoria).

### TAREA 5 — Verificar deploy workflow [si hay tiempo]

Confirmar que `.github/workflows/` referencia correctamente `backend/Dockerfile`. El Dockerfile está en `backend/Dockerfile` (verificado). Si los workflows apuntan a `./Dockerfile` (raíz) están mal; si apuntan a `./backend/Dockerfile` están bien.

### TAREA 6 — Actualizar CHANGELOG

Añadir entrada en `CHANGELOG.md` bajo `[Unreleased]`:
```
### Añadido
- Design system v2 (design_system.css, 894 líneas, tokens completos)
- Dashboard estilizado v2 (dashboard_structure.html)
- PWA v2 (sw_v2.js, manifest_v2.json, iconos, shortcuts, screenshots)
- STYLE_GUIDE.md y COMPONENT_GUIDE.md

### Corregido
- payroll.py: paginación ahora en BD (no en memoria)
- clock.py: rate limiter delegado a rate_limiter.py (sin stores locales)
```

---

## 5. ESTADO DE TESTS

### Backend tests (`backend/tests/`)
- **64 tests unitarios** en `test_api.py` + `test_security.py` — deberían pasar con `DATABASE_URL=sqlite+aiosqlite://` (in-memory).
- **`test_nfc_e2e.py`** (en `backend/`, no en `tests/`) — requiere backend corriendo en `localhost:8000`. **Falla si el servidor no está levantado.** No es un test de pytest estándar; es un script E2E manual.
- Último commit que los pasó todos: `cf20cfa` ("121/121 tests passing") — nota: ese conteo incluye tests de otras rondas; el estado actual del repo tiene 64 en `tests/` + el E2E.

**Para correr los tests:**
```bash
cd /c/Users/jordi/talentup-fichaje/backend
DATABASE_URL="sqlite+aiosqlite://" PIN_HASH_SALT="test-salt" JWT_SECRET="test-secret" \
  python -m pytest tests/ --tb=short -q
```
No correr `test_nfc_e2e.py` sin levantar el backend primero:
```bash
uvicorn app.main:app --port 8000 &
python test_nfc_e2e.py
```

### Frontend tests
- `frontend/tests/` — directorio existe (verificar contenido).
- `frontend/e2e/` — tests E2E con Playwright (`playwright.config.cjs`).
- `tests/e2e/` (raíz) — otro directorio E2E.

---

## 6. SCRIPTS Y HERRAMIENTAS DISPONIBLES

```bash
# Servir frontend
cd frontend && python -m http.server 3000

# Screenshots del dashboard
cd frontend && node screenshot-dashboard.mjs
cd frontend && node _shot.mjs

# Auditoría de landing
cd frontend && node _audit_landing.mjs

# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Tests backend
cd backend && DATABASE_URL="sqlite+aiosqlite://" python -m pytest tests/ -q

# Simular flow NFC
cd backend && python simulate_nfc_flow.py
```

---

## 7. DECISIONES PENDIENTES (requieren criterio)

1. **`dashboard_structure.html` vs `index.html`:** El nuevo dashboard usa nombres de página distintos (`reportes`, `incidencias`, `ajustes`) vs el actual (`informes`, `configuracion`, `calendario`, `vacaciones`, `bajas`). ¿Se reemplaza `index.html` con el nuevo dashboard? ¿Se mantiene ambos? ¿Se adapta `app.js`?

2. **`dashboard_new.html`:** Es una versión intermedia con JS demo y datos mock (1448 líneas, tiene `TODO(Jordi)` y `PENDIENTE DE DECISION`). ¿Se mergea con `dashboard_structure.html`? ¿Se descarta?

3. **`landing_new.html` vs `landing.html`:** Landing nueva rediseñada. ¿Reemplaza la actual?

4. **`sw_v2.js` / `manifest_v2.json`:** ¿Reemplazan a `sw.js` / `manifest.json`? ¿O se sirven en paralelo?

5. **Deploy:** El frontend está en Vercel (`vercel.json` config). El backend en Railway (`talentup-fichaje-backend.railway.app`). ¿El nuevo dashboard se deploya como `index.html` (reemplazando el actual) o como ruta nueva?

---

## 8. SCORES DE AUDITORÍA (referencia)

| Dimensión | Score | Nota |
|---|---|---|
| Backend FastAPI | 88/100 | PIN blocks Redis, rate limiting |
| Base de Datos | 86/100 | Payroll paginando en memoria |
| Seguridad | 84/100 | JWT cookies, XSS corregido, CSP nonce |
| Tests | 88/100 | 64/64 pasan, solo SQLite |
| DevOps | 74/100 | Deploy workflow path posiblemente roto |
| Frontend / PWA | 70/100 | Sin cambios desde V3 — **el dashboard v2 lo sube** |
| Multi-tenant | 72/100 | Sin cambios |
| **Global** | **86/100** | Objetivo: 88+ |

**Tu trabajo en el dashboard es lo que más puede mover la aguja del frontend (70 → 85+).**

---

## 9. ORDEN DE EJECUCIÓN RECOMENDADO

1. ✅ Leer este documento completo.
2. ✅ Leer `frontend/STYLE_GUIDE.md` y `frontend/COMPONENT_GUIDE.md`.
3. ✅ Leer `frontend/design_system.css` (tokens).
4. ✅ Leer `frontend/dashboard_structure.html` (esqueleto).
5. ✅ Leer `frontend/index.html` (referencia de ids/data-page que `app.js` espera).
6. 🔨 **Estilizar** `dashboard_structure.html` (TAREA 1).
7. 🔍 Verificar en navegador (servir + screenshot).
8. 🔨 Commitear frontend v2 (TAREA 2).
9. 🔨 Fix payroll paginación (TAREA 3) — si hay tiempo.
10. 🔨 Fix clock.py limpio (TAREA 4) — si hay tiempo.
11. 🔨 Verificar deploy workflow (TAREA 5) — si hay tiempo.
12. 🔨 Actualizar CHANGELOG (TAREA 6).
13. 🔨 Commit final con fixes de backend.
14. 🔨 Push a `origin/master`.

---

## 10. NOTAS FINALES

- **No inventes datos.** Si un archivo no existe, dilo. Si un test falla, reporta el error real.
- **Respeta el design system.** `design_system.css` es la fuente de verdad. No añadas colores, radios ni espacios que no estén definidos como tokens.
- **El naranja es acento.** Nunca fondo de superficie grande. Esta es la regla #1 del sistema.
- **No hay modo oscuro.** Decisión de producto. No lo implementes.
- **Los tests deben pasar.** Si tocas el backend, corre `pytest tests/` antes de commitear.
- **Commitea con mensajes descriptivos** en español o inglés (consistente con el repo).

---

*Generado por Hermes Agent · 08 Aug 2026 · `C:\Users\jordi\talentup-fichaje\CLAUDE_HANDOFF.md`*