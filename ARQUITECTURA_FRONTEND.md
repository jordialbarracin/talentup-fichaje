# Documento de Arquitectura Frontend — TalentUP Fichaje

**Versión:** 2.0 · **Fecha:** 2026-08-09 · **Dominio:** `talentup.es`

Este documento describe la arquitectura del frontend de TalentUP Fichaje: las ocho páginas que componen el producto, cómo se conectan entre sí, qué rutas sirven, qué tokens de diseño consumen y cómo se autentican contra el backend.

---

## 1. Visión general

El frontend de TalentUP es un conjunto de **páginas HTML estáticas** servidas por Vercel, sin framework de build ni SSR. Hay tres familias de superficies:

1. **Marketing / legales** — páginas públicas indexables: `landing_new`, `pricing`, `contacto`, `terminos`, `privacidad`.
2. **App de gestión** — SPA de administrador: `index.html` (escritorio) y `dashboard_new.html` (demo de diseño).
3. **PWA de fichaje** — dos clientes de empleado: `terminal/index.html` (kiosko NFC) y `mobile/index.html` (PWA móvil).

Todas las superficies importan **`design_system.css`** como única fuente de verdad de tokens de diseño (color, tipografía, espacio, sombra, movimiento). No hay dark mode; el sistema es *light* por decisión de marca.

El backend expone la API en `/api/*` (Railway en producción, `localhost:8080` en desarrollo). Vercel enruta `/api/(.*)` hacia el backend vía proxy en `vercel.json`, de modo que el frontend siempre llama a `/api/...` relativo.

---

## 2. Páginas del frontend

### 2.1 `landing_new.html` → `/` (home)

Landing pública de marketing. Es la **página de entrada** del sitio.

- **Ruta servida:** `/` (redirección permanente desde `/landing.html` y `/landing_new.html` en `vercel.json`).
- **Archivo físico:** `frontend/landing_new.html`.
- **SEO:** `canonical` → `https://talentup.es/`, `hreflang es` y `x-default`, Open Graph completo, `robots: index, follow`.
- **Tokens:** importa `design_system.css` y `manifest_v2.json`.
- **Enlaces salientes:** anclas internas (`#producto`, `#precios`, `#faq`, `#kit`), `pricing.html` (vía `#precios`), `contacto.html`, `terminos.html` (incluye `#dpa` y `#privacidad`), y `index.html` (login del panel).
- **Autenticación:** ninguna. Es pública.

### 2.2 `index.html` → `/` (app SPA de gestión)

El **panel de administración** real. Es una SPA de un solo archivo con un `src/app.js` modular (125 KB) que gestiona login, estado, navegación y todas las llamadas API.

- **Ruta servida:** `/` — en producción `vercel.json` enruta `/(.*)` a `index.html` como catch-all, de modo que la SPA se sirve en cualquier path no redirigido.
- **Archivo físico:** `frontend/index.html` + `frontend/src/app.js`.
- **Navegación interna:** la función `navigate(page)` conmuta `.page-content` por `data-page`. Nueve vistas: `dashboard`, `empleados`, `calendario`, `turnos`, `fichajes`, `vacaciones`, `bajas`, `informes`, `configuracion`. No usa router de URL (hash o history); el estado vive en `state.currentPage`.
- **Login:** formulario `#login-form` → `POST /api/auth/login` con `{ email, password }`. Botón demo (solo visible en `localhost`) → login real con `demo@talentup.es`.
- **Token de sesión:** el backend emite `access_token` (JWT) y `refresh_token` como **cookies httpOnly**. La SPA nunca lee el JWT en JS: usa `credentials: 'include'` en cada `fetch` y la cookie viaja sola. Existe un helper `getCookie('access_token')` solo para comprobar expiración (`isTokenExpired`), no para enviar el token.
- **API_BASE:** `window.location.hostname === 'localhost' ? 'http://localhost:8080/api' : '/api'`. En producción las llamadas son relativas y Vercel hace de proxy.
- **Endpoints consumidos:** `/auth/login`, `/auth/register`, `/auth/logout`, `/employees`, `/shifts`, `/schedules`, `/vacations`, `/leave`, `/calendar/holidays`, `/settings`, `/billing/status`, `/billing/checkout-session`, `/billing/portal`, `/reports/export`, entre otros.
- **PWA:** registra `sw_v2.js` (service worker con app-shell precacheada y cola offline IndexedDB para fichajes).

### 2.3 `dashboard_new.html` → `/dashboard` (demo de diseño)

Prototipo visual del nuevo dashboard. Es **estático y autocontenido**: datos demo en un array `EMPLOYEES` de 24 empleados, sin llamadas a la API.

- **Ruta servida:** `/dashboard` (según `sitemap_v2.xml`). En `vercel.json` cae al catch-all `/(.*)` → `index.html`; el archivo `dashboard_new.html` se sirve directo solo si se referencia explícitamente.
- **Archivo físico:** `frontend/dashboard_new.html`.
- **Navegación interna:** siete vistas con `data-view` (`dashboard`, `empleados`, `fichajes`, `turnos`, `reportes`, `incidencias`, `ajustes`) conmutadas por clase `.view.is-active`.
- **Tokens:** importa `design_system.css` (layout propio, tokens del sistema).
- **Autenticación:** ninguna. Es una maqueta de diseño, no producción.

### 2.4 `pricing.html` → `/pricing`

Página pública de planes y precios.

- **Ruta servida:** `/pricing` (canonical `https://talentup.es/pricing.html`).
- **Archivo físico:** `frontend/pricing.html`.
- **SEO:** `index, follow`, Open Graph, `canonical` y `hreflang`.
- **Tokens:** `design_system.css`.
- **Enlaces salientes:** `contacto.html`, `landing.html` (con anclas `#features`, `#faq`), `terminos.html`. Nota: `landing.html` es la landing antigua; `landing_new.html` es la vigente.
- **Autenticación:** ninguna.

### 2.5 `contacto.html` → `/contacto`

Formulario de contacto comercial y soporte.

- **Ruta servida:** `/contacto`.
- **Archivo físico:** `frontend/contacto.html`.
- **Enlaces salientes:** `index.html` (login), `landing_new.html` (`#producto`, `#precios`, `#faq`), `terminos.html` (`#dpa`, `#privacidad`).
- **Tokens:** `design_system.css` + `manifest_v2.json`.
- **Autenticación:** ninguna.

### 2.6 `terminos.html` → `/terminos`

Términos de Servicio (B2B SaaS).

- **Ruta servida:** `/terminos`.
- **Archivo físico:** `frontend/terminos.html`.
- **Estructura:** diez secciones ancla `#s1`–`#s10` más `#dpa` (DPA) y `#privacidad` (referencia a privacidad).
- **Enlaces salientes:** `contacto.html`, `index.html`, `landing_new.html`, `privacidad.html`.
- **Tokens:** `design_system.css`.
- **Autenticación:** ninguna. Indexable, `changefreq: yearly`.

### 2.7 `privacidad.html` → `/privacidad`

Política de Privacidad y Cookies (RGPD / LOPDGDD).

- **Ruta servida:** `/privacidad`.
- **Archivo físico:** `frontend/privacidad.html`.
- **Estructura:** diez secciones `#s1`–`#s10`. Enlaces externos a guías de cookies de Safari, Chrome, Edge y Firefox.
- **Enlaces salientes:** `contacto.html`, `index.html`, `landing_new.html`.
- **Tokens:** `design_system.css`.
- **Autenticación:** ninguna. Indexable, `changefreq: yearly`.

### 2.8 `terminal/index.html` → `/terminal/`

Kiosko de fichaje **NFC + PIN + QR**. Pensado para una tablet fijada en la pared del local.

- **Ruta servida:** `/terminal/` (subdirectorio estático en Vercel).
- **Archivo físico:** `terminal/index.html`.
- **Configuración persistida:** `localStorage` con dos claves: `talentup_config` (`{ backendUrl, tenantId }`) y `talentup_offline_queue` (cola de fichajes pendientes). El `backendUrl` por defecto es `http://localhost:8000`.
- **Pantallas:** `screenPin`, `screenLocked`, `screenAdmin`, `screenSetup` — kiosco autocontenido con bloqueo por intentos fallidos.
- **Autenticación del admin:** modal de login → `POST {backendUrl}/api/auth/login` (credenciales del owner). Las cookies httpOnly se setean en el dominio del backend.
- **Fichaje:** `POST {backendUrl}/api/clock` con `{ pin, type: 'auto', tenant_id }`. Si la red falla, encola en `localStorage` y reintentan con `syncPendingClocks()`.
- **NFC:** WebSocket a `{backendUrl}/ws/nfc` (convierte `http`→`ws`). Reconnect automático cada 5 s. Ping cada 30 s.
- **QR:** `POST {backendUrl}/api/clock/qr`.
- **Tokens:** importa `../frontend/design_system.css` (relativo). Layout propio del kiosco.

### 2.9 `mobile/index.html` → `/mobile/`

PWA del empleado para fichar desde su propio móvil.

- **Ruta servida:** `/mobile/` con `manifest` en `/mobile/manifest.json` e iconos en `/mobile/icons/`.
- **Archivo físico:** `mobile/index.html` + `mobile/manifest.json` + `mobile/sw.js`.
- **API_BASE:** `hostname === 'localhost' ? 'http://localhost:8000/api' : '/api'`.
- **Almacenamiento:** `localStorage` con claves prefijadas `talentup_mobile_*` (`tenant_id`, `tenant_name`, `pending` fichajes, `last_sync`).
- **Flujo:** selección de restaurante (`GET /api/tenants`) → validación de PIN (`POST /api/clock/verify`) → fichaje (`POST /api/clock`) → historial de hoy (`GET /api/clock/today`).
- **Autenticación:** **sin JWT**. El empleado se identifica por `tenant_id` + `pin`. La API de `/clock*` es pública por diseño (no requiere cookie de admin).
- **Offline:** cola `pendingClocks` en `localStorage`, sincronización automática al recuperar conexión.
- **Tokens:** importa `../frontend/design_system.css` (relativo).

---

## 3. Conexión entre páginas

```
landing_new ─┬─> pricing ─> contacto
             ├─> contacto
             ├─> terminos ─> privacidad
             └─> index.html (login admin)

index.html (admin SPA) ──/api──> backend Railway
   │
   └─ navigate() entre 9 vistas internas (sin router URL)

terminal/index ──/api + /ws/nfc──> backend (backendUrl configurable)
mobile/index   ──/api──> backend (tenant_id + pin, sin JWT)
dashboard_new  ── estático, sin backend
```

Las páginas públicas se enlazan entre sí por HTML relativo (`contacto.html`, `terminos.html`). En producción, `vercel.json` aplica redirecciones limpias: `/landing_new.html` → `/`. El `sitemap_v2.xml` declara las URLs canónicas indexables: `/`, `/pricing`, `/contacto`, `/dashboard`, `/terminos`, `/privacidad`.

---

## 4. Tokens de diseño (design_system.css)

Única fuente de verdad visual, importada por todas las páginas. Definida en `:root`:

- **Color:** `--brand: #FF6B35`, `--brand-hover: #E55A2B`, `--bg-app: #f5f5f7`, `--bg-surface: #fff`, `--text-primary: #1d1d1f`, `--success: #34C759`, `--danger: #FF3B30`, `--warning: #FF9500`, `--info: #007AFF`.
- **Tipografía:** `--font-sans` (SF Pro / system-ui), `--text-display` 34 px → `--text-micro` 11 px, con tracking `-0.03em` a `-0.01em`.
- **Espacio:** escala `--space-1` (4 px) a `--space-25` (100 px).
- **Radios:** `--radius-xs` 4 px → `--radius-pill` 980 px.
- **Sombra:** `--shadow-hairline`, `--shadow-card`, `--shadow-raised`, `--shadow-float`, `--shadow-modal`.
- **Movimiento:** `--dur-instant` 100 ms → `--dur-slow` 300 ms, con `--ease-out: cubic-bezier(0.16,1,0.3,1)`.
- **Z-index:** `--z-base` 1 → `--z-toast` 200.

El `manifest_v2.json` declara `theme_color: #FF6B35` (barra del SO) y repite los tokens de marca en `_meta.tokens` para referencia.

---

## 5. Tokens de autenticación

El backend emite dos JWT tras `POST /api/auth/login`:

| Token | Medio | Uso |
|---|---|---|
| `access_token` | Cookie httpOnly `access_token` | Autentica cada llamada `/api/*` del panel admin. La SPA envía `credentials: 'include'` y no lee el token en JS (salvo comprobación de expiración). |
| `refresh_token` | Cookie httpOnly `refresh_token` | Renueva el `access_token` vía `POST /api/auth/refresh` sin re-login. |

Los endpoints de fichaje (`/api/clock*`, `/api/clock/nfc`, `/api/clock/qr`, `/api/clock/verify`, `/api/tenants`) son **públicos**: se autentican por `tenant_id` + `pin`, no por JWT. Por eso `terminal` y `mobile` no manejan JWT. El `terminal` sí hace login de admin (para acceder al panel de configuración del kiosco), y ahí recibe las cookies httpOnly.

Rate limiting: 10 logins fallidos por IP cada 5 minutos; 30 operaciones de fichaje por minuto.

---

## 6. Service Worker y offline

`sw_v2.js` precachea el **app shell** (`index.html`, `design_system.css`, `src/app.js`, `i18n.js`, iconos, `manifest_v2.json`, `offline.html`). Estrategia cache-first para assets estáticos, network-first para `/api/`. Los métodos mutantes (POST/PUT/PATCH/DELETE) que fallan por red se encolan en IndexedDB (`talentup-offline-queue`) y se reintentan. `mobile/sw.js` y el `localStorage` del `terminal` replican la misma idea a nivel de cliente.

---

*Fin del documento. 1500 palabras aprox.*