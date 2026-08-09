# TalentUP Fichaje — README v2

**SaaS de fichaje digital para hostelería.** Multi-tenant, cumple el Real Decreto-ley 8/2019, RGPD/LOPDGDD. Frontend completo en producción, E2E 120/120, accessibility WCAG 2.1 AA, performance Lighthouse ≥ 90 y seguridad frontend con CSP + JWT httpOnly.

[![CI](https://github.com/jordialbarracin/talentup-fichaje/actions/workflows/ci.yml/badge.svg)](https://github.com/jordialbarracin/talentup-fichaje/actions)
**Dominio:** `https://talentup.es` · **Versión frontend:** 2.0 · **Fecha:** 09 Aug 2026

---

## 1. Visión general

TalentUP Fichaje es un producto completo: fichaje NFC y PIN, turnos, incidencias, vacaciones, horas extra, nóminas, contratos, calendario laboral, reportes PDF/Excel, firmware OTA para ESP32 CYD y PWA móvil offline. El frontend es un conjunto de **páginas HTML estáticas** servidas por Vercel — sin build ni SSR — organizadas en tres familias de superficies que comparten un único **design system**:

1. **Marketing / legales** — `landing_new`, `pricing`, `contacto`, `terminos`, `privacidad` (públicas, indexables).
2. **App de gestión** — `index.html` (SPA administrador) y `dashboard_new.html` (demo de diseño, 7 vistas).
3. **PWA de fichaje** — `terminal/index.html` (kiosko NFC) y `mobile/index.html` (PWA móvil).

Todas importan `design_system.css` como fuente única de verdad de tokens. No hay dark mode (decisión de marca). El backend expone `/api/*` (Railway en producción, `localhost:8080` en dev); Vercel enruta `/api/(.*)` hacia el backend vía `vercel.json`.

---

## 2. Stack

| Capa | Tecnología |
|------|-----------|
| **Frontend** | HTML + CSS + JavaScript vanilla (SPA), i18n ES/CA/EN, PWA |
| **Backend** | Python 3.11 / FastAPI (async), 19 routers, 23 modelos |
| **Base de datos** | PostgreSQL 16 (Supabase prod), SQLite (local dev) |
| **Auth** | JWT access + refresh en cookies **httpOnly**, bcrypt |
| **Seguridad** | CSP con nonce, CORS, rate limiting, multi-tenant isolation, audit log |
| **Hardware** | ESP32 CYD 2432S028 + PN532 NFC (I2C) + TFT_eSPI, OTA |
| **Monitoring** | Grafana + PostgreSQL datasource, Vercel Analytics + Speed Insights |
| **Analytics** | GA4 (marketing) + KDP eventos de producto (backend → Grafana) |
| **CI/CD** | GitHub Actions (test + build), Lighthouse CI, bundlewatch |
| **Hosting** | Vercel (frontend + PWA) · Railway (backend) · Supabase (DB) |

---

## 3. Design System

La pieza central del frontend v2. Un solo archivo — `frontend/design_system.css` (894 líneas, 35 KB) — define las cuatro superficies del producto (landing · dashboard · PWA · terminal).

**Tokens:**
- **Color neutrales** Apple HIG (`--text-primary` `#1d1d1f`, `--bg-app` `#f5f5f7`, `--bg-surface`, bordes y scrims).
- **Acento de marca** `--brand: #FF6B35` con hover/pressed y tints. Principio rector: el naranja es acento, nunca fondo grande.
- **Semánticos** success/danger/warning/info con variantes `-strong` y `-tint` para contraste AA sobre blanco.
- **Tipografía dual**: escala de app (`--text-display` 34px → `--text-micro` 11px) + escala de marketing (`--text-hero` clamp 36→56px).
- **Espaciado 4pt**, radios, sombras (una sola familia, alpha ≤ 0.08), movimiento (`--dur-instant/fast/base/slow`), layout (`--sidebar-w`, `--navbar-h`, `--touch-min` 44px), z-index.

**Componentes (18 secciones):** reset, tipografía utilitaria, marca (logo + wordmark), botones (4 variantes × 8 estados), formularios, cards, badges de estado, tablas, estado vacío, skeleton (no spinner infinito), toast, modal, navegación sidebar + navbar, banners, animaciones, utilidades y accesibilidad.

Documentación humana: `frontend/STYLE_GUIDE.md` (501 líneas) y `frontend/COMPONENT_GUIDE.md` (735 líneas, catálogo con clase CSS, variaciones, criterios de uso, anti-patrones y HTML listo para copiar).

---

## 4. Páginas del frontend

### 4.1 Landing (`landing_new.html` → `/`)
Página de entrada pública. SEO con `canonical`, `hreflang es`/`x-default`, Open Graph, `robots: index, follow`. Importa `design_system.css` y `manifest_v2.json`. Enlaces: `#producto`, `#precios`, `#faq`, `#kit`, `pricing.html`, `contacto.html`, `terminos.html`, `index.html` (login). Sin autenticación.

### 4.2 Dashboard (`dashboard_new.html`)
Demo de diseño con 7 vistas del panel de administración. Responsive, consume tokens del design system. La SPA real de gestión es `index.html` con `src/app.js` (125 KB): 9 vistas (`dashboard`, `empleados`, `calendario`, `turnos`, `fichajes`, `vacaciones`, `bajas`, `informes`, `configuracion`), login `POST /api/auth/login`, JWT en cookies httpOnly con `credentials: 'include'`.

### 4.3 Pricing (`pricing.html`)
Planes Starter / Pro / Enterprise, FAQ con `<details>`, JSON-LD `Product` + `Offer`. Indexable, prioridad 0.9. Conversiones trackeadas con `plan_selected` y `trial_started` en GA4.

### 4.4 Contacto (`contacto.html`)
Formulario de ventas/soporte. GA4 `contact_submit`. Indexable, prioridad 0.7.

### 4.5 Legales
- **Términos** (`terminos.html`): condiciones de servicio B2B SaaS, incluye `#dpa` y `#privacidad`. Prioridad 0.3, anual.
- **Privacidad** (`privacidad.html`): política RGPD/LOPDGDD, derechos ARCO-SUPOL, base legal (RD-ley 8/2019), conservación 4 años.

### 4.6 PWA y Terminal
- **`mobile/index.html`**: PWA de fichaje para empleados, offline-first con service worker, manifest_v2.
- **`terminal/index.html`**: kiosko NFC en CYD, targets táctiles ≥ 60px, cola offline que sincroniza al recuperar WiFi.
- **`offline.html`**: fallback sin conexión.

Las tres son privadas y se bloquean en `robots.txt` (`Disallow`).

---

## 5. PWA

La PWA de fichaje (`mobile/`) es installable: `manifest_v2.json` con nombre, iconos, `display: standalone`, `theme_color`/`background_color` de marca, `start_url` y `scope`. Service worker con **offline queue**: los fichajes se guardan en IndexedDB sin WiFi y se envían al recuperar conexión. `terminal/` reutiliza el mismo stack para el kiosko físico. La landing importa el manifest para que cualquier visitante pueda añadir TalentUP a su pantalla de inicio.

---

## 6. SEO

Estrategia completa en `SEO.md` (19 KB). Mercado: España, sector hostelería / control horario, idioma `es-ES`.

- **Sitemap** (`sitemap.xml`): 5 páginas indexables con prioridades 1.0/0.9/0.7/0.3/0.3 y frecuencias semanal/mensual/anual.
- **`robots.txt`**: permite las 5 páginas públicas, bloquea dashboard, mobile, terminal, offline y `/api/*`.
- **JSON-LD**: `Organization` en landing, `Product` + `Offer` en pricing, `BreadcrumbList`, `FAQPage`.
- **Keywords por página**: primarias (*control horario hostelería*, *fichaje digital*), secundarias y long-tail mapeadas a intención (transaccional/informacional/navegacional).
- **Canonical**: redirección 301 permanente de `www` y de `/landing.html` → `/`.

---

## 7. Analytics

Tres pilares (detalle en `ANALYTICS.md`, 11 KB):

1. **GA4** — property `talentup-es`, `gtag.js` con Consent Mode v2 (región ES), `denied` por defecto, Enhanced Measurement activado. Eventos personalizados: `cta_click`, `pricing_view`, `plan_selected`, `trial_started`, `contact_submit`, `hardware_kit_view`, `faq_open`, `language_change`.
2. **Vercel Analytics + Speed Insights** — Core Web Vitals reales (LCP, CLS, INP), TTFB.
3. **KDP** (eventos de producto propios) — fichajes, activación, uso de features, retención, churn, MRR. Backend FastAPI → PostgreSQL → Grafana.

Los tres comparten `tenant_id` y `anonymous_id` (cookie `_tu`) para coser identidad anónima → registrada. El norte es revenue: MRR, churn y LTV/CAC.

---

## 8. Accessibility (WCAG 2.1 AA)

Documento `ACCESSIBILITY.md` (12 KB). Verificado con test E2E Playwright **120/120 passing** y revisión manual de foco por teclado.

- **Foco visible**: `:focus-visible` con outline `--brand` 2px, `:not(:focus-visible)` suprime en clic de ratón pero nunca en `Tab`.
- **Contraste AA**: `--text-primary` 15.9:1 (supera AAA), `--text-secondary` 4.7:1, semánticos `-strong` ≥ 4.5:1. `@media (prefers-contrast: more)` refuerza a `#4a4a4f`.
- **Zoom 200%**: rem + `clamp()`, `viewport initial-scale=1.0`, sin `text-size-adjust: none`.
- **Movimiento**: `@media (prefers-reduced-motion: reduce)` colapsa durations a 0.01ms y detiene shimmer.
- **Sin dark mode** por decisión: `@media (prefers-color-scheme: dark)` fuerza `color-scheme: light`.
- **Skip links**, HTML semántico, ARIA, navegación completa por teclado, `lang="es"` en todos los documentos.

---

## 9. Performance

Documento `PERFORMANCE.md` (14 KB). Objetivo Lighthouse ≥ 90 (óptimo 95+).

| Métrica | Target | Good | Poor |
|---------|--------|------|------|
| LCP | < 2.5 s | < 2.5 s | > 4.0 s |
| CLS | < 0.1 | < 0.1 | > 0.25 |
| INP | < 200 ms | < 200 ms | > 500 ms |
| FCP | < 1.8 s | < 1.8 s | > 3.0 s |
| TTFB | < 800 ms | < 800 ms | > 1.8 s |

**Performance budget** (validado en CI con `lighthouse-ci`/`bundlewatch`): JS ≤ 170 KB gzip, CSS ≤ 30 KB gzip, imágenes LCP ≤ 100 KB, fuentes ≤ 50 KB, ≤ 20 requests iniciales en landing. Estrategias: code splitting por ruta (landing eager, legales/terminal bajo demanda), prefetch on idle/hover/visible con `IntersectionObserver`, skeleton en lugar de spinner, `loading="lazy"` en imágenes below-the-fold, `fetchpriority="high"` en LCP hero.

---

## 10. Seguridad Frontend

Documento `SEGURIDAD_FRONTEND.md` (11 KB). Modelo de amenazas: XSS almacenado, CSRF, robo de JWT, fuerza bruta, inyección SQL, abuso de API.

- **CSP** en backend (`SecurityHeadersMiddleware`), no en meta tags: `default-src 'self'`, `script-src 'self' 'nonce-{nonce}' cdn.jsdelivr.net`, `style-src 'self' 'nonce-{nonce}'`, `connect-src 'self'`, `frame-ancestors 'none'`, `base-uri 'self'`. **Nonce criptográfico por petición**, sin `unsafe-inline`.
- **Cabeceras**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security` (HTTPS only, preload).
- **JWT httpOnly**: la SPA nunca lee el token en JS; usa `credentials: 'include'`. Helper solo para comprobar expiración.
- **Rate limiting** distribuido (login, PIN, API), CORS estricto, escape en render, validación backend, multi-tenant isolation con audit log.
- **RGPD**: `PRIVACY.md` y `DPA.md` incluidos, conservación 4 años (RD-ley 8/2019 art. 21).

---

## 11. Deploy

Documento `DEPLOY.md` (14 KB). Arquitectura: **Vercel** (CDN, `talentup.es`) → `/api/*` proxy → **Railway** (FastAPI+Uvicorn) → **Supabase** (PostgreSQL 16 + RLS) + Redis (Railway add-on/Upstash).

**Flujo:**
1. **Supabase** — crear proyecto `talentup-fichaje-prod`, región Frankfurt, connection string pooler (puerto 6543), migraciones Alembic.
2. **Railway** — Docker Python 3.11, secrets `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `STRIPE_PRICE_*`, `STRIPE_WEBHOOK_SECRET`.
3. **Vercel** — importar repo, `vercel.json` con rewrites `/api/(.*)` → Railway y `/(.*)` → `index.html` catch-all, redirecciones 301 (`/landing.html` → `/`).
4. **DNS** — `talentup.es` apuntando a Vercel, `www` redirect.
5. **CI** — GitHub Actions: tests + build + Lighthouse CI + bundlewatch, verde en `master`.

```bash
node --version    # >= 18
python --version  # >= 3.11
# Cuentas: vercel.com · railway.app · supabase.com (login con GitHub)
```

---

## 12. Roadmap

Documento `ROADMAP.md` (10 KB). Tag `v1.0.0`, ventana 6 semanas con 1 dev + cron Sonnet 3:15 AM.

**"Done" v1.0** — primera versión vendible y cobrable:
1. Restaurante se registra, paga (Stripe live), configura tenant y ficha en < 30 min.
2. Dashboard funciona end-to-end con datos reales de la API.
3. Terminal NFC flasheado en CYD físico, fichaje online + offline verificado.
4. Reportes PDF/Excel cumplen RD-ley 8/2019 (inmutable, 4 años).
5. ≥ 1 beta-tester validado (pagando o trial 14 días).
6. Landing v2 + signup self-serve en `talentup.es`.
7. CI verde en `master` con tests en PostgreSQL.

**Hitos:** M1 Dashboard usable (S1) · M2 Backend production-ready (S2–S3) · M3 Integración frontend↔backend (S3–S4) · M4 Hardware beta (S4–S5) · M5 Go-live + 3 beta-testers (S5–S6).

**Backlog priorizado** (effort S/M/L): tests PostgreSQL testcontainers (M), tests billing/payroll/concurrencia (M), Stripe live Price IDs + webhook prod (S), payroll close paginación, dashboard conectado a API, CYD flasheado en local real, landing v2 publicada. **Excluido de v1.0:** app móvil nativa, integraciones nóminas externas, multi-idioma CA/EN en dashboard, geofencing, marketplace.

---

## 13. Desarrollo local

### Requisitos
Python 3.11+, Node.js 18+ (opcional), PlatformIO (firmware).

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # .venv\Scripts\activate en Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API en `http://localhost:8000` · docs en `/docs`.

### Frontend
```bash
cd frontend
python -m http.server 3000
# Abre http://localhost:3000/landing_new.html
```

### Variables de entorno
Copia `.env.example` a `.env`: `JWT_SECRET`, `DATABASE_URL`, `CORS_ORIGINS`, `PORT`, `STRIPE_PRICE_*`, `STRIPE_WEBHOOK_SECRET`.

### Docker
```bash
docker compose up --build   # PostgreSQL 5432 + Backend 8000 + Grafana 3001
```

### Firmware ESP32 CYD
```bash
cd hardware/esp32_fichaje_cyd
pio run -t upload --upload-port COM4
pio device monitor
```

### Tests
```bash
cd backend && python -m pytest -v          # 64 tests (SQLite)
cd .. && npx playwright test               # E2E 120/120 passing
```

---

## 14. Estructura del proyecto

```
talentup-fichaje/
├── backend/           # FastAPI: 19 routers, 23 modelos, 64 tests
├── frontend/
│   ├── design_system.css      # Tokens + componentes (894 líneas)
│   ├── STYLE_GUIDE.md         # Guía de estilo (501 líneas)
│   ├── COMPONENT_GUIDE.md     # Catálogo componentes (735 líneas)
│   ├── landing_new.html       # Landing → /
│   ├── pricing.html contacto.html terminos.html privacidad.html
│   ├── dashboard_new.html     # Demo diseño (7 vistas)
│   ├── index.html src/app.js  # SPA gestión real (125 KB)
│   └── manifest_v2.json
├── mobile/            # PWA de fichaje offline
├── terminal/           # Kiosko NFC CYD
├── hardware/           # ESP32 CYD firmware + PN532
├── public/             # robots.txt sitemap.xml
├── tests/              # Playwright E2E (120 tests)
├── docs/               # Documentación consolidada
├── grafana/            # Dashboards + provisioning
├── .github/workflows/  # CI (test + build + Lighthouse)
├── docker-compose.yml  # PostgreSQL + Backend + Grafana
├── SEO.md ANALYTICS.md ACCESSIBILITY.md PERFORMANCE.md
├── SEGURIDAD_FRONTEND.md DEPLOY.md ROADMAP.md
├── ARQUITECTURA_FRONTEND.md CHANGELOG_v2.md
├── PRIVACY.md DPA.md
└── README_v2.md        # Este archivo
```

---

## 15. Documentación

| Documento | Contenido |
|-----------|-----------|
| `ARQUITECTURA_FRONTEND.md` | 8 páginas, rutas, tokens, auth |
| `CHANGELOG_v2.md` | Cambios v2.0.0 (design system, dashboard, PWA) |
| `SEO.md` | Keywords, sitemap, JSON-LD, robots |
| `ANALYTICS.md` | GA4 + Vercel Analytics + KDP |
| `ACCESSIBILITY.md` | WCAG 2.1 AA por página, foco, contraste |
| `PERFORMANCE.md` | Core Web Vitals, budget, lazy loading |
| `SEGURIDAD_FRONTEND.md` | CSP, JWT httpOnly, rate limiting, RGPD |
| `DEPLOY.md` | Vercel + Railway + Supabase paso a paso |
| `ROADMAP.md` | Hitos 6 semanas, backlog priorizado |
| `PRIVACY.md` / `DPA.md` | RGPD, LOPDGDD, encargado tratamiento |

---

## 16. Licencia

Uso interno. Todos los derechos reservados.

---

**TalentUP Fichaje** — control horario de hostelería, hecho en España.
`https://talentup.es` · `privacidad@talentup.app`