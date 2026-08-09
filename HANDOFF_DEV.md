# HANDOFF_DEV — TalentUP Fichaje

> **Para:** nuevo desarrollador que se incorpora al proyecto.
> **Versión del documento:** 1.0 · **Fecha:** 09 Aug 2026
> **Repositorio:** `github.com/jordialbarracin/talentup-fichaje` · Rama: `master`
> **Local:** `C:\Users\jordi\talentup-fichaje`
> **README principal:** `README_v2.md` (léelo primero, este documento lo complementa).

Este es el documento que te habría gustado recibir el día uno. Describe qué existe, qué hace cada pieza, cómo se ejecuta el proyecto en local, qué falta para llegar a v1.0.0 y cómo continuar sin perderte. No asume que has leído el resto de la documentación.

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
├── backend/           # FastAPI: 19 routers, 23 modelos, 64 tests
├── frontend/          # Design system, SPA, landing, PWA assets
├── mobile/            # PWA de fichaje offline
├── terminal/          # Kiosko NFC CYD
├── hardware/          # ESP32 CYD firmware + PN532
├── public/            # robots.txt sitemap.xml
├── tests/             # Playwright E2E (120 tests)
├── docs/              # Documentación consolidada
├── grafana/           # Dashboards + provisioning
├── .github/workflows/ # CI (test + build + Lighthouse)
├── docker-compose.yml # PostgreSQL + Backend + Grafana
└── *.md               # Documentación (README_v2, ROADMAP, DEPLOY, etc.)
```

---

## 3. Archivos clave — qué hace cada uno

### 3.1 Backend (`backend/app/`)

```
main.py              — App FastAPI, lifespan, middleware (CSP nonce, rate limit, body limit)
auth.py              — JWT access+refresh, bcrypt, PIN hash (SHA256+bcrypt)
database.py          — Async engine, pool PG (20/40/30), init_db (Alembic en PG, create_all en SQLite)
rate_limiter.py      — Sliding window per IP+endpoint, PIN blocks con Redis + fallback memoria
rate_limit.py        — Decorador de rate limiting
tasks.py             — BackgroundTasks: payroll close, incident detection, report export
seed.py              — Datos de ejemplo
pagination.py        — Helper paginate() SQLAlchemy
rls.py               — Row-level security helpers
audit.py             — Audit log
metrics.py           — Prometheus
logging_config.py    — JSON logging
openapi_docs.py      — 718 líneas, OpenAPI/Swagger con response models y tags
migrate_pin_hash_fast.py
```

**Routers (19):** `auth, billing, calendar, clock, contracts, devices, employees, holidays, incidents, leave, notifications, overtime, payroll, reports, schedules, settings, shifts, tenants, vacations`

**Modelos (23):** `audit_log, billing_record, clock_in, contract, device, document_template, employee, geofence, holiday, incident, leave, notification, overtime, payroll, schedule, shift, tenant, user, vacation, vacation_request, work_calendar`

**Migraciones Alembic** en `backend/alembic/versions/`: initial, composite indexes, RLS tenant isolation, merge heads.

### 3.2 Frontend (`frontend/`)

```
index.html           — SPA en producción (1234 líneas, login + 9 vistas)
src/app.js           — Lógica SPA (3114 líneas): dashboard, empleados, calendario, turnos,
                       fichajes, vacaciones, bajas, informes, configuracion. Login POST /api/auth/login,
                       JWT en cookies httpOnly con credentials: 'include'
i18n.js              — ES/CA/EN (177 strings)
sw.js                — Service worker v1 (tracked)
manifest.json        — Manifest v1 (tracked)
landing.html         — Landing en producción (tracked)
terminos.html        — Términos de Servicio
contacto.html        — Contacto
offline.html         — Fallback offline
pricing.html         — Planes Starter/Pro/Enterprise + JSON-LD
privacidad.html      — Política RGPD/LOPDGDD

── NUEVO (v2, untracked) ──
design_system.css    — Design tokens completos (894 líneas, 35 KB) — FUENTE DE VERDAD
dashboard_new.html   — Demo de diseño (7 vistas)
landing_new.html     — Landing rediseñada (49 KB)
STYLE_GUIDE.md       — Guía de estilo (501 líneas)
COMPONENT_GUIDE.md   — Catálogo de componentes (735 líneas)
sw_v2.js             — Service worker v2 (cola offline IndexedDB)
manifest_v2.json     — Manifest PWA v2 (iconos, shortcuts, screenshots)
icon-*.svg           — Iconos nuevos (16,32,192,512,maskable,apple-touch)
shortcut-*.svg       — Shortcuts PWA (dashboard, empleados, fichajes, incidencias)
screenshot-*.svg     — Screenshots PWA (desktop, mobile)
```

### 3.3 Mobile y Terminal

- **`mobile/index.html`** — PWA de fichaje para empleados, offline-first con service worker, manifest_v2.
- **`terminal/index.html`** — Kiosko NFC en CYD, targets táctiles ≥ 60px, cola offline que sincroniza al recuperar WiFi.

### 3.4 Hardware (`hardware/`)

```
esp32_fichaje/       — Firmware ESP32 SPI (363 líneas)
esp32_fichaje_cyd/   — Firmware CYD 2432S028 + PN532 I2C + OTA + WDT + offline queue (911 líneas)
                       Compila en CI (PlatformIO). test/test_firmware.py
```

### 3.5 Tests

```
tests/e2e/           — Playwright E2E raíz (5 spec files: dashboard, landing, login, pwa, terminal)
frontend/e2e/        — Playwright E2E frontend (talentup.spec.cjs)
frontend/tests/      — Unit tests (vitest + jsdom)
backend/tests/       — 64 tests pytest (test_api.py + test_security.py)
backend/test_nfc_e2e.py — E2E NFC manual (requiere backend corriendo en :8000)
```

### 3.6 CI/CD (`.github/workflows/`)

```
ci.yml               — pytest + coverage + firmware build (PlatformIO)
backend-ci.yml       — CI backend
deploy-backend.yml  — Deploy Railway
deploy-frontend.yml — Deploy Vercel
```

### 3.7 Documentación

| Documento | Contenido |
|-----------|-----------|
| `README_v2.md` | Visión general, stack, estructura, dev local (léelo primero) |
| `ROADMAP.md` | Hitos 6 semanas, backlog priorizado 34 tareas |
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
```

### Variables de entorno
Copia `.env.example` a `.env` y rellena: `JWT_SECRET`, `DATABASE_URL`, `CORS_ORIGINS`, `PORT`, `STRIPE_PRICE_*`, `STRIPE_WEBHOOK_SECRET`, `PIN_HASH_SALT`, `REDIS_URL`.

### Docker (todo junto)
```bash
docker compose up --build   # PostgreSQL 5432 + Backend 8000 + Grafana 3001
```

### Tests
```bash
# Backend (64 tests, SQLite en memoria)
cd backend
DATABASE_URL="sqlite+aiosqlite://" PIN_HASH_SALT="test-salt" JWT_SECRET="test-secret" \
  python -m pytest tests/ --tb=short -q

# E2E Playwright (120 tests — requiere backend en :8000 y frontend en :3000)
npx playwright test

# Frontend unit (vitest)
cd frontend && npm test

# Firmware
cd hardware/esp32_fichaje_cyd
pio run -t upload --upload-port COM4
pio device monitor
```

⚠️ `test_nfc_e2e.py` requiere backend corriendo en `localhost:8000` antes de ejecutarse.

---

## 5. Qué falta para v1.0.0

El proyecto está en **v1.0.0-en-desarrollo**. El frontend v2 está completo y commiteado, los E2E pasan 120/120, pero hay trabajo pendiente. El camino crítico está en `ROADMAP.md` (34 tareas, 6 semanas con 1 dev + cron asistido).

### 🔴 Crítico / bloqueante

1. **Conectar el dashboard a la API real.** Hoy la SPA es estática. Falta el fetch a `/api/*` con JWT, loading/error/empty states. **Esto convierte el producto en vendible.**
2. **Alinear páginas con `app.js`.** El dashboard v2 usa nombres de página distintos a los que `app.js` espera (`reportes` vs `informes`, `incidencias` vs `configuracion`, etc.). Hay que alinear IDs o crear un mapeo.
3. **Login + registro self-serve.** Login con `/api/auth/*`, registro → Stripe Checkout (trial 14 días).
4. **Activar PWA v2.** Reemplazar `sw.js`/`manifest.json` con v2. Verificar cola offline IndexedDB.
5. **Publicar `landing_new.html` como `/`.** Actualizar `vercel.json`, redirección 301 de `/landing.html` → `/`.

### 🟡 Importante — backend production-ready

6. **Tests en PostgreSQL (testcontainers).** Los 64 tests solo corren en SQLite. Sin tests en PG no se deploya con confianza.
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

- **Backend:** 64 tests en `backend/tests/` pasan en SQLite. Coverage report en CI pero sin gate.
- **E2E:** 120/120 passing (Playwright, 5 spec files en `tests/e2e/` + `frontend/e2e/`).
- **Frontend unit:** vitest con jsdom en `frontend/tests/`.
- **CI:** `ci.yml` corre pytest + coverage + firmware build (PlatformIO, `continue-on-error`). No hay job de PostgreSQL ni gate de coverage.
- **Git:** rama `master` up to date con origin. Hay cambios sin commitear (frontend v2 modificado) y archivos untracked (docs v2).

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
- **No hay `pricing.html` independiente** — la sección de precios está integrada en `landing_new.html` con JSON-LD `Offer`.

Bienvenido al proyecto. El frontend está sólido; el trabajo ahora es integración backend↔frontend y productionización.

---

*TalentUP Fichaje — control horario de hostelería, hecho en España. `https://talentup.es` · `privacidad@talentup.app`*