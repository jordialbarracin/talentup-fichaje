# HANDOFF_DEV — TalentUP Fichaje

> **Para:** nuevo desarrollador que se incorpora al proyecto.
> **Versión del documento:** 2.0 · **Fecha:** 09 Aug 2026
> **Repositorio:** `github.com/jordialbarracin/talentup-fichaje` · Rama: `master`
> **Local:** `C:\Users\jordi\talentup-fichaje`
> **README principal:** `README_v2.md` (léelo primero, este documento lo complementa).
> **Estado git:** working tree limpio, HEAD `b360572`, todo el frontend v2 ya commiteado.

Este es el documento que te habría gustado recibir el día uno. Describe qué existe, qué hace cada pieza, cómo se ejecuta el proyecto en local, qué falta para llegar a v1.0.0 y cómo continuar sin perderte. No asume que has leído el resto de la documentación. Toda la información aquí está verificada contra el estado real del repositorio en el momento de escribir.

---

## 1. Qué es TalentUP Fichaje

SaaS de **fichaje digital para hostelería**. Multi-tenant, cumple el Real Decreto-ley 8/2019 (registro horario obligatorio, conservación 4 años) y RGPD/LOPDGDD. El producto completo cubre: fichaje NFC y PIN, turnos, incidencias, vacaciones, bajas, horas extra, nóminas, contratos, calendario laboral, reportes PDF/Excel, firmware OTA para ESP32 CYD y PWA móvil offline.

**Stack:**

| Capa | Tecnología |
|------|-----------|
| Frontend | HTML + CSS + JavaScript vanilla (SPA), i18n ES/CA/EN, PWA |
| Backend | Python 3.11 / FastAPI (async), 19 routers, 23 modelos |
| Base de datos | PostgreSQL 16 (Supabase prod), SQLite (local dev) |
| Auth | JWT access + refresh en cookies httpOnly, bcrypt |
| Hardware | ESP32 CYD 2432S028 + PN532 NFC (I2C) + TFT_eSPI, OTA |
| Monitoring | Grafana + PostgreSQL datasource |
| CI/CD | GitHub Actions (test + build + Lighthouse) |
| Hosting | Vercel (frontend) · Railway (backend) · Supabase (DB) |

**El frontend es un conjunto de páginas HTML estáticas** servidas por Vercel — sin build ni SSR — organizadas en tres familias que comparten un único design system (`design_system.css`).

---

## 2. Estructura del proyecto

```
talentup-fichaje/
├── backend/           # FastAPI: 19 routers, 23 modelos, 4 migraciones Alembic
├── frontend/          # Design system, SPA, landing, PWA assets
├── mobile/            # PWA de fichaje offline
├── terminal/          # Kiosko NFC CYD
├── hardware/          # ESP32 CYD firmware + PN532
├── public/            # robots.txt sitemap.xml
├── tests/             # Playwright E2E (5 spec files)
├── docs/              # Documentación consolidada (10 archivos)
├── grafana/           # Dashboards + provisioning
├── .github/workflows/ # CI (ci, backend-ci, deploy-backend, deploy-frontend)
├── docker-compose.yml # PostgreSQL + Backend + Grafana
└── *.md               # Documentación (README_v2, ROADMAP, DEPLOY, etc.)
```

---

## 3. Archivos clave — qué hace cada uno

### 3.1 Backend (`backend/app/`)

```
main.py (457 líneas)      — App FastAPI, lifespan, middleware (CSP nonce, rate limit, body limit)
auth.py (573 líneas)      — JWT access+refresh, bcrypt, PIN hash (SHA256+bcrypt)
database.py               — Async engine, pool PG (20/40/30), init_db (Alembic en PG, create_all en SQLite)
rate_limiter.py           — Sliding window per IP+endpoint, PIN blocks con Redis + fallback memoria
rate_limit.py             — Decorador de rate limiting
tasks.py                  — BackgroundTasks: payroll close, incident detection, report export
seed.py                   — Datos de ejemplo
pagination.py             — Helper paginate() SQLAlchemy
rls.py                    — Row-level security helpers
audit.py                  — Audit log
metrics.py                — Prometheus
logging_config.py         — JSON logging
openapi_docs.py (718 l.)  — OpenAPI/Swagger con response models y tags
migrate_pin_hash_fast.py  — Migración de hashes PIN
```

**Routers (19)** en `backend/app/routers/` — conteo de líneas verificado:

| Router | Líneas | Responsabilidad |
|--------|--------|-----------------|
| `reports.py` | 1068 | Reportes horas, incidencias, PDF, Excel |
| `clock.py` | 800 | Fichaje PIN, NFC, toggle in/out |
| `auth.py` | 573 | Login, register, me, refresh |
| `billing.py` | 456 | Stripe, planes, suscripciones |
| `employees.py` | 392 | CRUD empleados + asignación NFC |
| `shifts.py` | 266 | CRUD turnos |
| `overtime.py` | 263 | Horas extra, cálculo |
| `vacations.py` | 179 | Vacaciones: listar, crear, aprobar, rechazar |
| `leave.py` | 215 | Bajas y permisos |
| `contracts.py` | 208 | Contratos, tipos, renovaciones |
| `schedules.py` | 200 | Horarios, filtrado por fecha |
| `notifications.py` | 170 | Notificaciones in-app |
| `holidays.py` | 159 | Festivos |
| `incidents.py` | 155 | Detección de incidencias |
| `payroll.py` | 136 | Nóminas: listar, cerrar |
| `tenants.py` | 145 | Multi-tenant (super_admin) |
| `calendar.py` | 142 | Calendario laboral, generación |
| `devices.py` | 99 | Dispositivos NFC |
| `settings.py` | 79 | Configuración tenant |

**Modelos (23)** en `backend/app/models/`: `audit_log, billing_record, clock_in, contract, device, document_template, employee, geofence, holiday, incident, leave, notification, overtime, payroll, schedule, shift, tenant, user, vacation, vacation_request, work_calendar`.

**Migraciones Alembic** en `backend/alembic/versions/` (4 archivos): `9b16fa110308_initial.py`, `1a2b3c4d5e6f_add_composite_indexes.py`, `a15b29a48457_enable_rls_tenant_isolation.py`, `4af19aaef1cc_merge_heads.py`.

### 3.2 Frontend (`frontend/`)

```
index.html (1234 líneas)     — SPA en producción, login + 9 vistas, <style> inline
src/app.js (3114 líneas)     — Lógica SPA: dashboard, empleados, calendario, turnos,
                                fichajes, vacaciones, bajas, informes, configuracion.
                                Login POST /api/auth/login, JWT en cookies httpOnly con
                                credentials: 'include'
i18n.js                      — ES/CA/EN (177 strings)
sw.js                        — Service worker v1 (tracked)
manifest.json                — Manifest v1 (tracked)
landing.html                 — Landing en producción (tracked)
terminos.html                — Términos de Servicio
contacto.html                — Contacto
offline.html                 — Fallback offline
pricing.html                 — Planes Starter/Pro/Enterprise + JSON-LD
privacidad.html              — Política RGPD/LOPDGDD

── Frontend v2 (commiteado en b360572) ──
design_system.css (898 l.)   — Design tokens completos — FUENTE DE VERDAD
dashboard_new.html (1609 l.) — Dashboard v2 con 7 vistas
dashboard_structure.html     — Esqueleto del dashboard (estructura sin estilos propios)
landing_new.html (1099 l.)   — Landing rediseñada
STYLE_GUIDE.md (501 l.)      — Guía de estilo
COMPONENT_GUIDE.md (735 l.)  — Catálogo de componentes
sw_v2.js                     — Service worker v2 (cola offline IndexedDB)
manifest_v2.json             — Manifest PWA v2 (iconos, shortcuts, screenshots)
icon-*.svg                   — Iconos nuevos (16,32,192,512,maskable,apple-touch)
shortcut-*.svg               — Shortcuts PWA (dashboard, empleados, fichajes, incidencias)
screenshot-*.svg             — Screenshots PWA (desktop, mobile)
vercel.json                  — Config de deploy Vercel (rutas /api/* → backend)
```

### 3.3 Mobile y Terminal

- **`mobile/index.html`** — PWA de fichaje para empleados, offline-first con service worker, manifest_v2, iconos 192/512.
- **`terminal/index.html`** — Kiosko NFC en CYD, targets táctiles ≥ 60px, cola offline que sincroniza al recuperar WiFi.

### 3.4 Hardware (`hardware/`)

```
esp32_fichaje/               — Firmware ESP32 SPI (363 líneas, standalone)
  esp32_fichaje.ino
  platformio.ini
  INFORME_TECNICO.md, README.md
esp32_fichaje_cyd/           — Firmware CYD 2432S028 + PN532 I2C + OTA + WDT + offline queue
  src/esp32_fichaje_cyd.ino  (911 líneas, 25 KB — compila en CI con PlatformIO)
  test/test_firmware.py      (42 KB — tests de firmware)
  platformio.ini
```

### 3.5 Tests

```
tests/e2e/                   — Playwright E2E raíz (5 spec files)
  test_dashboard.spec.js
  test_landing.spec.js
  test_login.spec.js
  test_pwa.spec.js
  test_terminal.spec.js
frontend/e2e/                — Playwright E2E frontend (talentup.spec.cjs)
frontend/tests/              — Unit tests (vitest + jsdom): app.test.js, setup.js
backend/tests/               — pytest (test_api.py 121 funcs, test_security.py 16 funcs, conftest.py)
backend/test_nfc_e2e.py      — E2E NFC manual (requiere backend corriendo en :8000)
backend/simulate_nfc_flow.py — Simulación de flow NFC
```

### 3.6 CI/CD (`.github/workflows/`)

```
ci.yml               — pytest + coverage + firmware build (PlatformIO, continue-on-error)
backend-ci.yml       — CI backend
deploy-backend.yml   — Deploy Railway
deploy-frontend.yml  — Deploy Vercel
```

### 3.7 Documentación

| Documento | Contenido |
|-----------|-----------|
| `README_v2.md` | Visión general, stack, estructura, dev local (léelo primero) |
| `ROADMAP.md` | Hitos 6 semanas, backlog priorizado 34 tareas, camino crítico |
| `DEPLOY.md` | Vercel + Railway + Supabase paso a paso |
| `ARQUITECTURA_FRONTEND.md` | 8 páginas, rutas, tokens, auth |
| `CHANGELOG_v2.md` | Cambios v2.0.0 (design system, dashboard, PWA) |
| `SEO.md` | Keywords, sitemap, JSON-LD, robots |
| `ANALYTICS.md` | GA4 + Vercel Analytics + KDP |
| `ACCESSIBILITY.md` | WCAG 2.1 AA por página, foco, contraste |
| `PERFORMANCE.md` | Core Web Vitals, budget, lazy loading |
| `SEGURIDAD_FRONTEND.md` | CSP, JWT httpOnly, rate limiting, RGPD |
| `PRIVACY.md` / `DPA.md` | RGPD, LOPDGDD, encargado tratamiento |
| `CLAUDE_HANDOFF.md` | Handoff previo (cron Opus 22:00) |

---

## 4. Cómo se ejecuta en local

### Requisitos
Python 3.11+, Node.js 18+ (opcional, para Playwright), PlatformIO (firmware).

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # .venv\Scripts\activate en Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API en `http://localhost:8000` · docs interactivas en `/docs`.

### Frontend
```bash
cd frontend
python -m http.server 3000
# Abre http://localhost:3000/landing_new.html (landing)
#        http://localhost:3000/index.html        (SPA gestión)
#        http://localhost:3000/dashboard_new.html (dashboard v2 demo)
```

### Variables de entorno
Copia `.env.example` a `.env` y rellena: `APP_ENV`, `LOG_LEVEL`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `CORS_ORIGINS`, `PORT`, `STRIPE_PRICE_*`, `STRIPE_WEBHOOK_SECRET`, `PIN_HASH_SALT`, `FIRMWARE_OTA_TOKEN`.

### Docker (todo junto)
```bash
docker compose up --build   # PostgreSQL 5432 + Backend 8000 + Grafana 3001 (admin/talentup)
```

### Tests
```bash
# Backend (SQLite en memoria)
cd backend
DATABASE_URL="sqlite+aiosqlite://" PIN_HASH_SALT="test-salt" JWT_SECRET="test-secret" \
  python -m pytest tests/ --tb=short -q

# E2E Playwright (requiere backend en :8000 y frontend en :3000)
npx playwright test

# Frontend unit (vitest)
cd frontend && npm test

# Firmware
cd hardware/esp32_fichaje_cyd
pio run -t upload --upload-port COM4
pio device monitor
```

⚠️ `test_nfc_e2e.py` requiere backend corriendo en `localhost:8000` antes de ejecutarse. No es un test pytest estándar; es un script E2E manual.

---

## 5. Qué falta para v1.0.0

El proyecto está en **v1.0.0-en-desarrollo**. El frontend v2 está completo y commiteado (commit `b360572`), pero hay trabajo pendiente. El camino crítico está en `ROADMAP.md` (34 tareas, 6 semanas con 1 dev + cron asistido).

### 🔴 Crítico / bloqueante

1. **Conectar el dashboard a la API real.** Hoy la SPA (`index.html` + `src/app.js`) es estática con datos mock. Falta el fetch a `/api/*` con JWT, loading/error/empty states. **Esto convierte el producto en vendible.**
2. **Alinear páginas con `app.js`.** El dashboard v2 (`dashboard_new.html`) usa nombres de página distintos a los que `app.js` espera (`reportes` vs `informes`, `incidencias` vs `configuracion`, etc.). Hay que alinear IDs o crear un mapeo.
3. **Login + registro self-serve.** Login con `/api/auth/*`, registro → Stripe Checkout (trial 14 días).
4. **Activar PWA v2.** Reemplazar `sw.js`/`manifest.json` con v2. Verificar cola offline IndexedDB.
5. **Publicar `landing_new.html` como `/`.** Actualizar `vercel.json`, redirección 301 de `/landing.html` → `/`.

### 🟡 Importante — backend production-ready

6. **Tests en PostgreSQL (testcontainers).** Los tests solo corren en SQLite. Sin tests en PG no se deploya con confianza.
7. **Tests de billing, payroll, concurrencia.** 0 tests de estos routers críticos.
8. **Stripe live.** `_get_price_id()` usa placeholders dev. Configurar `STRIPE_PRICE_*` en Railway.
9. **Payroll close: paginación en BD.** `payroll.py:23-69` carga `.all()` y pagina en Python. Migrar a `paginate()`.
10. **Limpiar `clock.py` rate limiter.** Eliminar stores locales duplicados (`_pin_limits`, etc.), delegar a `rate_limiter.py`.
11. **Secrets de producción en Railway.** Hoy son placeholders. Configurar `JWT_SECRET`, `DATABASE_URL`, `REDIS_URL`, `STRIPE_*`, `CORS_ORIGINS`.
12. **PostgreSQL gestionada (Supabase).** Migrar de SQLite a Supabase (UE, RGPD). `alembic upgrade head`. Verificar RLS.

### 🟢 Hardware (semanas 4–5)

13. **Flashear CYD físico + smoke test.** Compila en CI pero no se ha flasheado en CYD real.
14. **Provisioning de dispositivos.** Falta pairing: el CYD debe obtener `tenant_id` + `device_token` al arrancar.
15. **NFC E2E: tarjeta → CYD → backend → dashboard.** Valida la promesa central del producto.

### Excluido de v1.0
App móvil nativa, integraciones nóminas externas, multi-idioma CA/EN en dashboard, geofencing, marketplace.

---

## 6. Estado de tests y CI

- **Backend:** 121 funciones test en `test_api.py` + 16 en `test_security.py` pasan en SQLite (in-memory). Coverage report en CI pero sin gate.
- **E2E:** Playwright con 5 spec files en `tests/e2e/` (dashboard, landing, login, pwa, terminal) + `frontend/e2e/talentup.spec.cjs`.
- **Frontend unit:** vitest con jsdom en `frontend/tests/app.test.js`.
- **Firmware:** `test_firmware.py` (42 KB) en `hardware/esp32_fichaje_cyd/test/`.
- **CI:** `ci.yml` corre pytest + coverage + firmware build (PlatformIO, `continue-on-error`). No hay job de PostgreSQL ni gate de coverage.
- **Git:** rama `master` up to date con origin. Working tree limpio. Último commit `b360572` ya incluye todo el frontend v2 (design system, dashboard, landing, PWA, SEO, accessibility, performance, seguridad, docs).

---

## 7. Decisiones de diseño que debes respetar

1. **El naranja (`--brand: #FF6B35`) es acento, nunca fondo de superficie grande.** Tintes al 6–12%. Es la regla #1 del design system.
2. **Sin dark mode.** Decisión de producto. `@media (prefers-color-scheme: dark)` fuerza `color-scheme: light`.
3. **`design_system.css` es la fuente de verdad.** Todo valor vivo como `var(--token)`. No hardcodear colores, radios ni espacios.
4. **Sin gradientes decorativos, sin sombras dramáticas.** Una sola familia de sombras (alpha ≤ 0.08).
5. **Targets táctiles ≥ 44px** en app, **≥ 60px** en kiosco.
6. **Una sola acción primaria por pantalla.**
7. **JWT httpOnly.** La SPA nunca lee el token en JS; usa `credentials: 'include'`.
8. **CSP con nonce** en backend (`SecurityHeadersMiddleware`), no en meta tags. Sin `unsafe-inline`.

---

## 8. Cómo continuar (orden recomendado)

1. **Lee `README_v2.md`** completo (visión, stack, estructura).
2. **Lee `ROADMAP.md`** (34 tareas, 6 semanas, camino crítico).
3. **Levanta el proyecto en local** (sección 4 de este doc). Verifica que backend arranca y tests pasan.
4. **Explora el design system:** `frontend/design_system.css` + `STYLE_GUIDE.md` + `COMPONENT_GUIDE.md`.
5. **Abre la SPA:** `frontend/index.html` con `src/app.js` (3114 líneas). Mira los `data-page` y las funciones de cada vista.
6. **Ataca el camino crítico:** F3 (conectar dashboard a API) → F5 (login/signup) → M2 (trial self-serve).
7. **Backend:** sigue ROADMAP B1–B7 en paralelo (tests PG, Stripe live, fixes de auditoría).
8. **Commitea con mensajes descriptivos.** Si tocas el backend, corre `pytest tests/` antes de commitear.
9. **No inventes datos.** Si un archivo no existe, dilo. Si un test falla, reporta el error real.

---

## 9. Notas finales

- **Scores de auditoría (referencia):** Global 84–88/100. Backend 88, BD 86, Seguridad 84, Tests 88, DevOps 74, Frontend/PWA 70 (el dashboard v2 lo sube), Multi-tenant 72.
- **Cron asistido:** hay un cron nocturno (Sonnet 3:15 AM) que itera sobre la estilización del dashboard. Revisa sus commits cada mañana.
- **Hosting actual:** frontend en Vercel (`talentup.es`), backend en Railway, DB pendiente de migrar a Supabase. Hay un duplicado en GitHub Pages que debería desactivarse (SEO duplicado).
- **No hay `pricing.html` independiente publicado** — la sección de precios está integrada en `landing_new.html` con JSON-LD `Offer` (aunque `pricing.html` existe como archivo).
- **El frontend v2 ya está commiteado** (commit `b360572`). El trabajo ahora es integración backend↔frontend y productionización, no estilización desde cero.

Bienvenido al proyecto. El frontend está sólido; el trabajo ahora es integración backend↔frontend y productionización.

---

*TalentUP Fichaje — control horario de hostelería, hecho en España. `https://talentup.es` · `privacidad@talentup.app`*