# Changelog — TalentUP Fichaje

Todos los cambios notables del proyecto se documentan aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [2.0.0] — 2026-08-08

### Añadido — Sistema de diseño

- **`frontend/design_system.css`** (894 líneas, 35 KB): hoja de tokens central que es la fuente de verdad de las cuatro superficies del producto (landing · dashboard · PWA empleado · terminal kiosco). Un solo archivo, cuatro superficies.
  - **Tokens de color neutrales** (`--text-primary` `#1d1d1f` … `--text-quaternary`, `--bg-app` `#f5f5f7`, `--bg-surface`, `--bg-sunken`, `--bg-hover`, `--bg-pressed`, `--bg-scrim`, `--border` / `--border-strong` / `--border-hairline`). Valores hex de Apple HIG como fuente de verdad, no convertidos a OKLCH por decisión de producto.
  - **Acento de marca** (`--brand` `#FF6B35`, `--brand-hover`, `--brand-pressed`, tints `--brand-tint-06/08/12/35`). Principio rector: el naranja es acento, nunca fondo de superficie grande.
  - **Semánticos** (`--success` `#34C759` / `--success-strong` `#248A3D` / `--success-tint`, `--danger` `#FF3B30` / `--danger-hover` / `--danger-tint`, `--warning` `#FF9500` / `--warning-strong` / `--warning-tint`, `--info` `#007AFF` / `--info-tint`). Variantes `-strong` para contraste AA sobre blanco.
  - **Tipografía dual**: escala de app (`--text-display` 34px … `--text-micro` 11px) + escala de marketing (`--text-hero` clamp 36→56px, `--text-section` 28→40px, `--text-lead` 17→20px). Tokens de tracking (`--tracking-tight` … `--tracking-label`) y leading (`--leading-tight` … `--leading-relaxed`).
  - **Espaciado en escala 4pt** (`--space-1` 4px … `--space-25` 100px), **radios** (`--radius-xs` 4px … `--radius-2xl` 16px, `--radius-pill` 980px), **sombras** (una sola familia, nada más oscuro que alpha 0.08), **movimiento** (`--dur-instant/fast/base/slow`, easings), **layout** (`--sidebar-w`, `--sidebar-rail-w`, `--navbar-h`, `--container`, `--measure`, `--touch-min` 44px), **z-index** (`--z-base` … `--z-toast`).
  - **18 secciones de componentes**: reset/base, tipografía utilitaria, marca (logo + wordmark), botones (4 variantes × 8 estados), formularios, superficies (cards), badges de estado, tablas, estado vacío, carga (skeleton, no spinner infinito), toast, modal, navegación (sidebar + navbar), banners, animaciones, utilidades, accesibilidad y medios.
  - **Sin modo oscuro** por decisión de producto (sección 9.2 del doc de visión); si el navegador fuerza uno, se mantiene la superficie clara.

- **`frontend/STYLE_GUIDE.md`** (501 líneas, 26 KB): guía de estilo humana que documenta el sistema de diseño en prosa.
  - Cuatro principios de diseño (naranja como acento, claridad bajo presión, confianza silenciosa, un solo sistema cuatro superficies).
  - Paleta completa en tablas (neutrales, acento de marca, semánticos) con token, HEX y uso de cada color.
  - Tipografía (familias, escalas app vs marketing, tracking, leading), espaciado, radios, sombras, movimiento.
  - Reglas de accesibilidad (targets ≥ 44px app / ≥ 60px kiosco, contraste AA, foco visible), nomenclatura de tokens.

- **`frontend/COMPONENT_GUIDE.md`** (735 líneas, 28 KB): catálogo de componentes de UI definidos en `design_system.css`, con clase CSS, variaciones, criterios de uso, anti-patrones y ejemplo HTML listo para copiar.
  - 12 categorías: botones, inputs y formularios, cards (superficies), tablas, badges de estado, modales, toasts, navegación, skeletons y carga, estado vacío, banners, tipografía utilitaria.
  - Cada componente incluye cuándo usar, cuándo NO usar y snippet HTML.

### Añadido — Landing

- **`frontend/landing_new.html`** (912 líneas, 49 KB): nueva landing que consume `design_system.css` (todo color y tipo referencia un token; el archivo solo aporta composición, nunca valores sueltos).
  - SEO completo: meta description, keywords, canonical, hreflang `es` + `x-default`, Open Graph, Twitter Cards, `theme-color`.
  - **Datos estructurados JSON-LD**: `SoftwareApplication` con ofertas (Starter 29 €/mes, Pro 99 €/mes, Enterprise 499 €/mes) + `FAQPage` con 6 preguntas (RGPD, hardware, wifi, nóminas, cancelación, soporte). Se retiró el `aggregateRating` fabricado (4.8/120) de la versión anterior — se reincorpora cuando existan reviews verificables.
  - **Sección de pricing integrada** (planes Starter / Pro / Enterprise con sus features, kit NFC 49 € una sola vez, 14 días de prueba sin tarjeta). Esta sección cumple el rol de `pricing.html` dentro de la landing.
  - Header con lockup de marca, navegación y CTA "Probar gratis"; hero, producto, features, testimonial-ready, FAQ, footer.
  - Animación `reveal` para aparición progresiva de secciones.

### Añadido — Dashboard

- **`frontend/dashboard_structure.html`** (915 líneas, 45 KB): estructura del panel de gestión (app shell). No declara estilos: solo estructura y componentes sobre `design_system.css` (estilización posterior vía cron a las 22:00).
  - App shell con sidebar colapsable (logo + wordmark, navegación por secciones: Equipo, Gestión).
  - Iconos SVG reutilizables como `<symbol>` (mark, empty-people, empty-doc, empty-calendar) para los estados vacíos.
  - Navegación: Dashboard, Empleados, Fichajes, Turnos, Reportes, Incidencias.
  - `skip-link` de accesibilidad, `meta robots noindex,nofollow`, PWA meta tags.

### Añadido — PWA

- **`frontend/manifest_v2.json`** (161 líneas, 4.3 KB): manifest v2 de la PWA.
  - `id`, `name`, `short_name`, `description`, `lang` `es`, `dir` `ltr`, `theme_color` `#FF6B35`, `background_color` `#FFFFFF`, `display` `standalone` con `display_override` (standalone → minimal-ui → browser), `start_url` con UTM, `scope`, `orientation` `portrait-primary`.
  - `categories` (productivity, business, utilities).
  - **6 iconos**: `icon-16.svg`, `icon-32.svg`, `icon-192.svg` (any maskable), `icon-512.svg` (any maskable), `icon-maskable.svg` (maskable), `apple-touch-icon.svg` (180).
  - **4 shortcuts**: Dashboard (Hoy), Fichajes, Empleados (Equipo), Incidencias (Alertas), cada uno con icono `shortcut-*.svg` 96×96 y UTM.
  - **2 screenshots**: móvil (`screenshot-mobile-dashboard.svg` 1080×1920 narrow) y escritorio (`screenshot-desktop-dashboard.svg` 1280×800 wide).
  - `launch_handler` (navigate-existing), `edge_side_panel` (480px), `i18n` true, `prefer_related_applications` false.
  - `_meta` con `version` 2.0.0, referencia al `design_system.css` y al `talentup_design_vision.md`, y los tokens clave de color.

- **`frontend/sw_v2.js`** (293 líneas, 12 KB): service worker v2 con tokens del design system.
  - **Cache versionado** `talentup-fichaje-v2` con tres caches: `static`, `api`, `runtime`.
  - **App shell v2** pre-cachea los ficheros del nuevo design system (`design_system.css`, `dashboard_structure.html`, `manifest_v2.json`, iconos SVG nuevos, shortcuts).
  - **Estrategias**: cache-first para assets estáticos (css/js/svg/png/woff2…), network-first para `/api/`.
  - **Cola offline de fichajes** en IndexedDB (`talentup-offline-queue` / `pending-clockings`): los POST/PUT/PATCH/DELETE que fallan por red se encolan y se sincronizan con `sync` event.
  - **Fallback offline** con la paleta del design system (`--brand`, `--bg-app`, `--bg-surface`, `--text-primary`, `--text-secondary`, `--danger`, `--success`). Tema claro, no hay modo oscuro (principio 9.2).
  - Limpieza de caches antiguas en `activate`, `skipWaiting` y `clients.claim`.

### Añadido — Iconos y assets PWA

- `frontend/icon-16.svg`, `frontend/icon-32.svg` (favicons nuevos).
- `frontend/icon-maskable.svg` (512×512 maskable).
- `frontend/apple-touch-icon.svg` (180×180).
- `frontend/shortcut-dashboard.svg`, `shortcut-fichajes.svg`, `shortcut-empleados.svg`, `shortcut-incidencias.svg` (iconos de shortcuts 96×96).
- `frontend/screenshot-mobile-dashboard.svg` (1080×1920), `frontend/screenshot-desktop-dashboard.svg` (1280×800) para el manifest.
- `frontend/_audit_landing.mjs`, `frontend/_shot.mjs` (scripts de auditoría y captura de la landing).

### Cambiado

- `frontend/landing.html`: landing anterior modificada (sin reemplazar; `landing_new.html` es la sucesora).
- `frontend/contacto.html`, `frontend/terminos.html`: actualizados al nuevo design system.
- `frontend/icon-192.svg`, `frontend/icon-512.svg`: rediseñados con la nueva marca.
- `frontend/vercel.json`: configuración de deploy actualizada.
- `landing.html` (raíz): landing de producción actualizada.
- `robots.txt`, `sitemap.xml`: añadidos en la raíz para SEO.

### Notas

- **`pricing.html`** no existe como archivo independiente: la sección de precios (Starter / Pro / Enterprise) está integrada dentro de `landing_new.html`, con datos estructurados JSON-LD `Offer` y bloque visual de planes. Si se necesita una página dedicada, extraer la sección existente.
- **Cron de estilización a las 22:00**: `dashboard_structure.html` aporta estructura sin estilos; la estilización sobre `design_system.css` se aplica de forma programada (comentario en la cabecera del archivo).
- **Fuente de diseño**: `talentup_design_vision.md` (8 agosto 2026) es el documento de visión del que derivan `design_system.css`, `STYLE_GUIDE.md` y `COMPONENT_GUIDE.md`.

---

## [1.0.0] — 2026-08-07

### Añadido
- JWT refresh tokens (7 días) con endpoint `/api/auth/refresh`
- Rate limiting middleware (sliding window per IP+endpoint)
- DPA.md (Data Processing Agreement RGPD Art.28)
- Grafana monitoring (docker-compose + provisioning + dashboard)
- GitHub Actions CI/CD (test + coverage + firmware build)
- i18n frontend ES/CA/EN (177 strings traducibles)
- Firmware CYD 2432S028 completo (911 líneas): TFT_eSPI + PN532 I2C + OTA + WDT + offline queue (SPIFFS)
- 68 tests nuevos para 7 routers (tenants, contracts, schedules, overtime, payroll, notifications, calendar)
- OpenAPI/Swagger documentation con response models y tags grouping
- Landing page mejorada: SEO, JSON-LD, pricing, features, FAQ, responsive

### Cambiado
- PRIVACY.md actualizado (referencias Supabase/Vercel)
- README.md reescrito con documentación profesional y API reference
- .gitignore: excluido .pio/ y archivos sensibles
- Auth: tokens ahora incluyen campo "type" (access/refresh)
- Login y register ahora devuelven refresh_token además de access_token

### Corregido
- Conflictos de merge resueltos en main.py y auth.py

## [0.9.0] — 2026-07-19

### Añadido
- Backend FastAPI con 16 routers
- 49 tests iniciales (auth, employees, clock, shifts, vacations, leave, holidays, reports, security, incidents)
- Frontend SPA (index.html 129KB)
- Landing page inicial
- Firmware ESP32 SPI (363 líneas)
- Docker compose con PostgreSQL
- PRIVACY.md inicial
- Multi-tenant, JWT auth, bcrypt, audit log