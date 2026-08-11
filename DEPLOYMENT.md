# Guía de Despliegue — TalentUP Fichaje

**Versión:** 2.0.0 · **Fecha:** 09 Aug 2026 · **Stack:** Frontend → Vercel · Backend → Railway · DB → PostgreSQL · Cache → Redis · Monitoring → Grafana

> Guía completa de despliegue del SaaS multi-tenant de fichaje para hostelería. El frontend SPA (HTML/JS vanilla + PWA) se publica en Vercel (`talentup.es`), el backend FastAPI en Railway (`talentup-fichaje-backend.railway.app`), PostgreSQL como base de datos y Redis para caché/colas/rate-limiting. Se incluye además un duplicado estático en GitHub Pages y monitorización con Grafana.

---

## Tabla de contenidos

1. [Arquitectura de despliegue](#1-arquitectura-de-despliegue)
2. [Prerrequisitos](#2-prerrequisitos)
3. [Variables de entorno](#3-variables-de-entorno)
4. [Despliegue del backend en Railway](#4-despliegue-del-backend-en-railway)
5. [Despliegue del frontend en Vercel](#5-despliegue-del-frontend-en-vercel)
6. [Despliegue del duplicado en GitHub Pages](#6-despliegue-del-duplicado-en-github-pages)
7. [Configuración DNS](#7-configuración-dns)
8. [SSL/TLS](#8-ssltls)
9. [Monitorización (Grafana y logs)](#9-monitorización-grafana-y-logs)
10. [Procedimiento de rollback](#10-procedimiento-de-rollback)
11. [Checklist post-deploy](#11-checklist-post-deploy)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Arquitectura de despliegue

```
┌──────────────────┐   HTTPS    ┌──────────────────┐   TCP 5432  ┌──────────────┐
│   Vercel (CDN)   │ ─────────> │  Railway (API)   │ ─────────> │ PostgreSQL  │
│  talentup.es     │  /api/*     │  FastAPI+Uvicorn │            │  (RLS multi- │
│  SPA + PWA       │  proxy      │  Docker Python   │            │   tenant)    │
└──────────────────┘             └──────────────────┘            └──────────────┘
        │                                │
        │ HTTPS                          │  TCP 6379
        v                                v
┌──────────────────┐             ┌──────────────┐
│  GitHub Pages    │             │    Redis      │
│  (duplicado      │             │ (Railway add- │
│   estático)      │             │  on / Upstash)│
└──────────────────┘             └──────────────┘
                                         │
                                         v
                                 ┌──────────────┐
                                 │   Grafana     │
                                 │  (dashboards) │
                                 └──────────────┘
```

**Componentes del despliegue:**

| Capa | Servicio | Recurso | URL / Endpoint |
|------|----------|---------|----------------|
| Frontend principal | Vercel | Static + PWA (HTML/JS vanilla) | `https://talentup.es` |
| Frontend duplicado | GitHub Pages | Static (mirror) | `https://<usuario>.github.io/talentup-fichaje/` |
| Backend API | Railway | Docker (Python 3.11-slim) | `https://talentup-fichaje-backend.railway.app` |
| Base de datos | PostgreSQL 14+ | Multi-tenant + RLS | interno |
| Cache/Colas | Redis 7 | Rate-limit, refresh token revocation, health checks | interno Railway |
| Monitoring | Grafana | Dashboards provisioning | `http://localhost:3001` (local) |

> **Nota sobre el frontend:** El frontend es una SPA sin build (HTML/JS vanilla + service worker PWA). No requiere `npm run build`. Vercel y GitHub Pages sirven los archivos estáticos tal cual.

---

## 2. Prerrequisitos

### 2.1 Versiones de software requeridas

```bash
python --version    # >= 3.11
node --version      # >= 18
git --version       # >= 2.30
docker --version    # >= 24 (opcional, para build local)
```

| Software | Versión mínima | Uso |
|----------|----------------|-----|
| Python | 3.11+ | Backend FastAPI, migraciones Alembic |
| Node.js | 18+ | CLI de Vercel (`vercel`), CLI de Railway (`@railway/cli`) |
| PostgreSQL | 14+ | Base de datos de producción (recomendado 16) |
| Redis | 7+ | Cache distribuido, rate limiting, revocación de tokens |
| Docker | 24+ (opcional) | Build y prueba local de la imagen del backend |
| PlatformIO Core | 6+ (opcional) | Compilación del firmware ESP32 CYD |

### 2.2 Cuentas y accesos necesarios

- **Vercel** (`vercel.com`) — login con GitHub. Aloja el frontend en `talentup.es`.
- **Railway** (`railway.app`) — login con GitHub. Aloja el backend FastAPI + Redis add-on.
- **GitHub** — repositorio del proyecto. Activa CI/CD y GitHub Pages.
- **Proveedor DNS** (Cloudflare, Namecheap, etc.) — gestión del dominio `talentup.es`.
- **Stripe** (`dashboard.stripe.com`) — claves de API y webhook para pagos.

### 2.3 Verificación local

```bash
# Clonar el repositorio
git clone https://github.com/<usuario>/talentup-fichaje.git
cd talentup-fichaje

# Verificar el entorno
python --version    # 3.11.x o superior
node --version      # v18.x o superior

# Instalar CLI de Vercel y Railway
npm install -g vercel @railway/cli

# Login
vercel login        # OAuth con GitHub
railway login       # OAuth con GitHub
```

---

## 3. Variables de entorno

El proyecto define todas sus variables en `.env.example`. En producción se configuran como **secrets en Railway** (nunca en el repositorio).

### 3.1 Variables del backend

| Variable | Descripción | Ejemplo producción |
|----------|-------------|--------------------|
| `APP_ENV` | Entorno de ejecución | `production` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `LOG_FORMAT` | Formato de logs | `json` |
| `PORT` | Puerto del servidor (Railway lo inyecta) | `8000` |
| `BACKEND_URL` | URL pública del backend | `https://talentup-fichaje-backend.railway.app` |
| `DATABASE_URL` | Connection string PostgreSQL | `postgresql+asyncpg://user:pass@host:5432/talentup_fichaje` |
| `REDIS_URL` | Connection string Redis | `redis://...` (Railway la inyecta vía add-on) |
| `JWT_SECRET` | Secreto para firmar JWT | `openssl rand -hex 32` |
| `JWT_EXPIRE_MINUTES` | Expiración access token (min) | `480` (8 horas) |
| `JWT_REFRESH_EXPIRE_DAYS` | Expiración refresh token (días) | `30` |
| `PIN_HASH_SALT` | Sal para hash rápido de PIN | `openssl rand -hex 16` |
| `CORS_ORIGINS` | Orígenes permitidos (coma-separado) | `https://talentup.es,https://www.talentup.es` |
| `FRONTEND_URL` | URL pública del frontend | `https://talentup.es` |
| `STRIPE_SECRET_KEY` | Clave secreta Stripe (live) | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Secreto del webhook Stripe | `whsec_...` |
| `STRIPE_PRICE_BASIC` | Price ID plan Basic | `price_1ABC...` |
| `STRIPE_PRICE_PRO` | Price ID plan Pro | `price_1DEF...` |
| `STRIPE_PRICE_KIT` | Price ID plan Kit | `price_1GHI...` |

> **Seguridad:** `JWT_SECRET`, `PIN_HASH_SALT` y `STRIPE_SECRET_KEY` son secretos críticos. Genéralos con `openssl rand -hex 32` y guárdalos en Railway Variables ( Settings → Variables). **Nunca los subas al repositorio** — el `.gitignore` ya excluye `.env`.

### 3.2 Generación de secretos

```bash
# JWT_SECRET (64 caracteres hex)
openssl rand -hex 32

# PIN_HASH_SALT (32 caracteres hex)
openssl rand -hex 16

# Contraseña de base de datos
openssl rand -base64 24
```

---

## 4. Despliegue del backend en Railway

### 4.1 Crear proyecto en Railway

```bash
# Desde el directorio del backend
cd /c/Users/jordi/talentup-fichaje/backend

# Inicializar proyecto de Railway
railway init     # crea proyecto "talentup-fichaje"
```

Railway detecta automáticamente `backend/railway.json`:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 30
  }
}
```

### 4.2 Dockerfile (multi-stage, non-root)

El `backend/Dockerfile` usa build multi-stage con `python:3.11-slim`:

- **Builder stage:** instala dependencias en un venv aislado (`/opt/venv`).
- **Runtime stage:** usuario non-root `talentup` (UID/GID 1000), sin compiladores.
- **Healthcheck:** `curl -fsS http://127.0.0.1:${PORT:-8000}/api/health` cada 30s.
- **Comando:** `uvicorn app.main:app --host 0.0.0.0 --port 8000` (Railway reescribe `$PORT`).

### 4.3 Añadir PostgreSQL y Redis

```bash
# Añadir PostgreSQL como add-on en Railway
railway add       # selecciona "PostgreSQL" → se inyecta DATABASE_URL

# Añadir Redis como add-on en Railway
railway add       # selecciona "Redis" → se inyecta REDIS_URL
```

> **Importante:** `REDIS_URL` es **obligatorio en producción**. Si falta, el backend falla al arrancar con `RuntimeError: REDIS_URL requerido en produccion`. El health check `/api/health` verifica Redis con `ping`.

### 4.4 Configurar variables de entorno

```bash
# Obligatorias
railway variables set APP_ENV=production
railway variables set LOG_LEVEL=INFO
railway variables set LOG_FORMAT=json
railway variables set BACKEND_URL="https://talentup-fichaje-backend.railway.app"

# Base de datos (Railway la inyecta al añadir PostgreSQL; ajusta el driver)
railway variables set DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/talentup_fichaje"

# Seguridad
railway variables set JWT_SECRET="$(openssl rand -hex 32)"
railway variables set PIN_HASH_SALT="$(openssl rand -hex 16)"
railway variables set JWT_EXPIRE_MINUTES=480
railway variables set JWT_REFRESH_EXPIRE_DAYS=30

# CORS y frontend
railway variables set CORS_ORIGINS="https://talentup.es,https://www.talentup.es"
railway variables set FRONTEND_URL="https://talentup.es"

# Stripe (modo live)
railway variables set STRIPE_SECRET_KEY="sk_live_..."
railway variables set STRIPE_WEBHOOK_SECRET="whsec_..."
railway variables set STRIPE_PRICE_BASIC="price_..."
railway variables set STRIPE_PRICE_PRO="price_..."
railway variables set STRIPE_PRICE_KIT="price_..."
```

> **DATABASE_URL:** Railway inyecta la URL de PostgreSQL automáticamente al añadir el add-on. Asegúrate de que use el driver `postgresql+asyncpg://` (async). Si Railway la inyecta como `postgresql://`, reescríbela a `postgresql+asyncpg://` para que SQLAlchemy async la acepte.

### 4.5 Aplicar migraciones (Alembic)

Las migraciones viven en `backend/alembic/versions/`:

| Revisión | Descripción |
|----------|-------------|
| `9b16fa110308` | Esquema inicial (tablas, relaciones) |
| `1a2b3c4d5e6f` | Índices compuestos para rendimiento |
| `4af19aaef1cc` | Merge heads |
| `a15b29a48457` | RLS multi-tenant (Row Level Security) |

```bash
cd /c/Users/jordi/talentup-fichaje/backend

# Instalar dependencias en un venv temporal
python -m venv .venv-deploy
source .venv-deploy/bin/activate      # Linux/Mac
# .venv-deploy\Scripts\activate        # Windows
pip install -r requirements.txt

# Apuntar Alembic a la BD de producción
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/talentup_fichaje"

# Ejecutar migraciones
python -m alembic upgrade head

# Verificar revisión actual
python -m alembic current
# Debe mostrar: a15b29a48457 (head)
```

### 4.6 Verificar RLS (Row Level Security)

La migración `a15b29a48457` habilita RLS en 13 tablas con la política `tenant_isolation`:

```sql
-- Tablas con RLS: employees, clock_ins, shifts, schedules, vacation_requests,
-- leaves, holidays, overtime, payroll, notifications, contracts, incidents,
-- devices, billing_records

-- Verificar que RLS está activo:
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND rowsecurity = true;

-- Debe devolver las 13 tablas con rowsecurity = true
```

La política compara `tenant_id` con la variable de sesión `app.tenant_id`:

```sql
CREATE POLICY tenant_isolation ON {table}
USING (tenant_id = current_setting('app.tenant_id')::text);
```

### 4.7 Desplegar

```bash
railway up      # construye la imagen Docker y despliega
```

Railway construirá la imagen Docker (tarda ~3-5 min). Asigna automáticamente una URL pública: `https://talentup-fichaje-backend.railway.app`.

### 4.8 Verificar el backend

```bash
# Health check (deep: DB + Redis + uptime)
curl https://talentup-fichaje-backend.railway.app/api/health
# Esperado: {"status":"healthy","version":"1.0.0","db_status":"ok","redis_status":"ok",...}

# Métricas operativas (JSON)
curl https://talentup-fichaje-backend.railway.app/api/metrics

# Métricas Prometheus (para scraping)
curl https://talentup-fichaje-backend.railway.app/api/metrics/prometheus
```

> Si el health check devuelve `503` con `status: "degraded"`, revisa los logs (`railway logs`). El error más común es `REDIS_URL requerido en produccion` — añade el add-on Redis.

### 4.9 Configuración Procfile (alternativa)

Railway usa `railway.json` por defecto, pero también soporta `Procfile`. Si prefieres un `Procfile` en `backend/`:

```procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
release: python -m alembic upgrade head
```

- `web:` proceso principal del servidor.
- `release:` se ejecuta antes de cada despliegue (migraciones automáticas).

> **Recomendado:** usa `railway.json` (ya configurado) para control explícito del healthcheck. El `Procfile` es una alternativa si necesitas ejecutar migraciones en la fase `release`.

---

## 5. Despliegue del frontend en Vercel

### 5.1 Configuración de `vercel.json`

El `frontend/vercel.json` ya está configurado:

```json
{
  "version": 2,
  "domains": ["talentup.es", "www.talentup.es"],
  "redirects": [
    { "source": "/www.talentup.es/(.*)", "destination": "https://talentup.es/$1", "permanent": true },
    { "source": "/landing.html", "destination": "/", "permanent": true },
    { "source": "/landing_new.html", "destination": "/", "permanent": true }
  ],
  "builds": [
    { "src": "index.html", "use": "@vercel/static" },
    { "src": "public/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "https://talentup-fichaje-backend.railway.app/api/$1" },
    { "src": "/robots.txt", "dest": "/public/robots.txt" },
    { "src": "/sitemap.xml", "dest": "/public/sitemap.xml" },
    { "src": "/manifest.json", "dest": "/manifest.json" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

**Puntos clave:**

- **Build command:** ninguno (frontend estático sin compilación).
- **Output directory:** `frontend/` (Vercel sirve `index.html` y `public/`).
- **Proxy `/api/*`:** enruta las llamadas de la API al backend de Railway. Evita problemas de CORS y hardcoding de URLs.
- **Headers de seguridad:** `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `X-Robots-Tag`.
- **Redirects:** `landing.html` y `landing_new.html` → `/` (301 permanente).

### 5.2 Despliegue desde la CLI

```bash
cd /c/Users/jordi/talentup-fichaje/frontend

# Despliegue de preview (primera vez)
vercel          # responde: Link to existing project? No → "talentup-fichaje"

# Despliegue a producción
vercel --prod
```

### 5.3 Configurar el dominio `talentup.es`

1. **Vercel dashboard → talentup-fichaje → Settings → Domains.**
2. **Add:** `talentup.es` y `www.talentup.es`.
3. En tu proveedor DNS, configura los registros (ver [§7 Configuración DNS](#7-configuración-dns)).
4. Espera a que Vercel valide el DNS (verde en el dashboard, ~5 min).

### 5.4 Variables de entorno del frontend

El frontend es estático pero referencia la URL del API de forma relativa (`/api/...`). El proxy de `vercel.json` enruta `/api/*` al backend de Railway, por lo que **no se necesitan variables de entorno en Vercel** para la URL del API.

Verifica que no haya URLs hardcodeadas a `localhost`:

```bash
cd /c/Users/jordi/talentup-fichaje/frontend
grep -rn "localhost" index.html i18n.js sw.js sw_v2.js
# Si hay resultados, reemplaza por el proxy /api/ (recomendado)
```

### 5.5 Verificar el frontend

```bash
# Frontend carga
curl -o /dev/null -w "%{http_code}" https://talentup.es
# → 200

# PWA manifest accesible
curl -o /dev/null -w "%{http_code}" https://talentup.es/manifest.json
# → 200

# Service worker accesible
curl -o /dev/null -w "%{http_code}" https://talentup.es/sw_v2.js
# → 200

# Proxy API funciona
curl https://talentup.es/api/health | jq .status
# → "healthy"
```

---

## 6. Despliegue del duplicado en GitHub Pages

El repositorio incluye `.github/workflows/deploy-frontend.yml`, un workflow de GitHub Actions que publica el contenido de `frontend/` en GitHub Pages como duplicado estático.

### 6.1 Workflow de GitHub Pages

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend to GitHub Pages
on:
  push:
    branches: [master]
    paths: ['frontend/**', '.github/workflows/deploy-frontend.yml']
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: "pages"
  cancel-in-progress: true
jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Pages
        uses: actions/configure-pages@v5
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: frontend
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 6.2 Activar GitHub Pages

1. **Repositorio → Settings → Pages.**
2. **Source:** GitHub Actions (no "Deploy from a branch").
3. El workflow se ejecuta automáticamente en cada push a `master` que toque `frontend/`.
4. La URL será `https://<usuario>.github.io/talentup-fichaje/`.

> **Limitación:** GitHub Pages es un duplicado estático. El proxy `/api/*` de `vercel.json` **no funciona en GitHub Pages** (no soporta rewrites dinámicos). Este duplicado sirve como respaldo del frontend pero las llamadas a la API fallarán a menos que configures una URL absoluta al backend de Railway.

### 6.3 Consideraciones del duplicado

- **No es un reemplazo de Vercel.** Es un respaldo para casos de caída del CDN de Vercel.
- **Sin PWA completa:** el service worker puede no registrarse correctamente en el path `/talentup-fichaje/`.
- **SEO:** `robots.txt` y `sitemap.xml` deben apuntar a `talentup.es` (dominio canónico).

---

## 7. Configuración DNS

### 7.1 Registros para Vercel (frontend principal)

En tu proveedor DNS (Cloudflare recomendado para gestión sencilla):

| Tipo | Nombre | Valor | Propósito |
|------|--------|-------|-----------|
| A | `@` (talentup.es) | `76.76.21.21` | Vercel edge network |
| CNAME | `www` | `cname.vercel-dns.com` | Redirección www → apex |
| CNAME | `api` | `talentup-fichaje-backend.railway.app` | (opcional) Dominio custom del backend |

> **Verificación:** confirma los valores A/CNAME actuales en el dashboard de Vercel (Settings → Domains), ya que Vercel puede sugerir IPs distintas según la región.

### 7.2 Registros para Railway (backend, opcional)

Si configuras un dominio custom para el backend (`api.talentup.es`):

1. **Railway → Settings → Networking → Custom Domain** → `api.talentup.es`.
2. Añade el CNAME en tu DNS apuntando a `railway.app`.
3. Railway genera automáticamente el certificado SSL (ver [§8 SSL/TLS](#8-ssltls)).

### 7.3 Verificación DNS

```bash
# Verificar que el dominio apunta a Vercel
dig talentup.es +short
# → 76.76.21.21

dig www.talentup.es +short
# → cname.vercel-dns.com

# Verificar propagación global
nslookup talentup.es 8.8.8.8
```

---

## 8. SSL/TLS

### 8.1 Vercel (frontend)

Vercel genera y renueva automáticamente certificados SSL/TLS (Let's Encrypt) para todos los dominios añadidos. **No se requiere configuración manual.**

- **Protocolo:** TLS 1.3 (preferido), TLS 1.2 (fallback).
- **HSTS:** el backend envía `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` cuando `APP_ENV=production` o el proxy indica HTTPS.
- **Redirección HTTP → HTTPS:** activada por defecto en Vercel.

### 8.2 Railway (backend)

Railway provee TLS automático en la URL `*.railway.app`. Para dominios custom, Railway genera el certificado automáticamente al validar el CNAME.

### 8.3 Verificación SSL

```bash
# Verificar certificado del frontend
openssl s_client -connect talentup.es:443 -servername talentup.es </dev/null 2>/dev/null \
  | openssl x509 -noout -dates -issuer

# Verificar HSTS
curl -sI https://talentup.es | grep -i strict-transport-security
# → strict-transport-security: max-age=31536000; includeSubDomains; preload

# Verificar TLS del backend
curl -sI https://talentup-fichaje-backend.railway.app/api/health | grep -i strict-transport-security
```

---

## 9. Monitorización (Grafana y logs)

### 9.1 Grafana (local / self-hosted)

El `docker-compose.yml` incluye Grafana con provisioning automático:

```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  environment:
    GF_SECURITY_ADMIN_USER: admin
    GF_SECURITY_ADMIN_PASSWORD: talentup
    GF_USERS_ALLOW_SIGN_UP: "false"
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning
    - ./grafana/dashboards:/var/lib/grafana/dashboards
```

**Arrancar Grafana local:**

```bash
docker compose up -d grafana
# Acceso: http://localhost:3001
# Usuario: admin / Contraseña: talentup (¡cámbiala en producción!)
```

**Provisioning:**

- **Datasource:** PostgreSQL (`grafana/provisioning/datasources/datasources.yml`).
- **Dashboard:** `talentup_overview.json` se carga automáticamente desde `grafana/dashboards/`.

### 9.2 Métricas del backend

El backend expone dos endpoints de métricas:

| Endpoint | Formato | Uso |
|----------|---------|-----|
| `/api/metrics` | JSON | Métricas operativas (uptime, requests hoy, errores 5xx, tenants activos, empleados) |
| `/api/metrics/prometheus` | Prometheus | Scraping con Prometheus/Grafana |

**Métricas expuestas (Prometheus):**

- `http_requests_total{method,endpoint,status}` — contador de peticiones HTTP.
- `http_request_duration_seconds{method,endpoint}` — histograma de duración.
- `active_connections` — conexiones activas.
- Contadores diarios (requests, errors).

**Configurar scraping en Grafana/Prometheus:**

```yaml
# prometheus.yml (si usas Prometheus externo)
scrape_configs:
  - job_name: 'talentup-backend'
    scrape_interval: 15s
    metrics_path: /api/metrics/prometheus
    static_configs:
      - targets: ['talentup-fichaje-backend.railway.app']
```

### 9.3 Logs

El backend usa logging estructurado en JSON (`LOG_FORMAT=json` en producción):

- **Nivel:** configurable con `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR).
- **Formato:** JSON con campos `event`, `method`, `path`, `status_code`, `duration_ms`, `request_id`.
- **Request ID:** cada petición recibe un `X-Request-ID` (UUID) para trazabilidad.

```bash
# Ver logs de Railway
railway logs

# Ver logs filtrados por nivel
railway logs --filter "ERROR"

# Ejemplo de log JSON:
# {"event":"request","method":"POST","path":"/api/auth/login","status_code":200,
#  "duration_ms":45.2,"request_id":"a1b2c3d4-..."}
```

### 9.4 Health check profundo

El endpoint `/api/health` verifica tres subsistemas:

```json
{
  "status": "healthy",        // "degraded" si algo falla
  "service": "TalentUP Fichaje API",
  "version": "1.0.0",
  "started_at": "2026-08-09T10:00:00Z",
  "uptime_seconds": 3600,
  "db_status": "ok",          // SELECT 1
  "redis_status": "ok"        // PING
}
```

- **HTTP 200** si todo está OK.
- **HTTP 503** si DB o Redis fallan (`status: "degraded"`).

Configura un monitor de uptime (UptimeRobot, BetterUptime) sobre `https://talentup.es/api/health`.

---

## 10. Procedimiento de rollback

### 10.1 Rollback del backend (Railway)

```bash
# Listar deployments recientes
railway status

# Rollback al deployment anterior
railway rollback    # lista deployments, selecciona el anterior
```

Railway mantiene un historial de deployments. Cada rollback reasigna la URL a la imagen anterior.

### 10.2 Rollback del frontend (Vercel)

```bash
# Listar deployments
vercel ls

# Promocionar un deployment anterior a producción
vercel promote <deployment-url>
```

### 10.3 Rollback de base de datos (Alembic)

```bash
cd /c/Users/jordi/talentup-fichaje/backend
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/talentup_fichaje"

# Rollback una revisión
python -m alembic downgrade -1

# Rollback a una revisión específica
python -m alembic downgrade 9b16fa110308

# Ver historial
python -m alembic history
```

> **Precaución:** los rollbacks de BD pueden causar pérdida de datos. Siempre haz un backup antes de un downgrade en producción.

### 10.4 Rollback del firmware ESP32

El firmware no tiene rollback automático. Procedimiento:

1. Compila la versión anterior: `git checkout <commit> && pio run -t upload`.
2. El OTA de ArduinoOTA sobrescribe la flash completa.

### 10.5 Procedimiento de rollback completo (incidente crítico)

1. **Detectar:** alerta de health check fallido o error 5xx masivo.
2. **Comunicar:** notificar al equipo (Slack/email).
3. **Rollback backend:** `railway rollback` al último deployment estable.
4. **Rollback frontend:** `vercel promote <url-estable>`.
5. **Verificar:** `curl https://talentup.es/api/health` → `status: healthy`.
6. **Investigar:** revisar logs (`railway logs`) y métricas (Grafana).
7. **Corregir:** aplicar fix en una rama separada, probar, desplegar.
8. **Postmortem:** documentar causa raíz y acciones preventivas.

---

## 11. Checklist post-deploy

### 11.1 Backend

- [ ] Railway: proyecto creado, PostgreSQL y Redis conectados
- [ ] Railway: todas las variables de entorno configuradas (DB, JWT, PIN_HASH_SALT, CORS, Stripe)
- [ ] Railway: `DATABASE_URL` usa driver `postgresql+asyncpg://`
- [ ] Railway: `REDIS_URL` inyectada (add-on Redis añadido)
- [ ] Alembic: migraciones aplicadas (`alembic upgrade head`)
- [ ] Alembic: RLS verificado (13 tablas con `rowsecurity = true`)
- [ ] Health check: `curl https://talentup-fichaje-backend.railway.app/api/health` → `healthy`
- [ ] Métricas: `/api/metrics/prometheus` devuelve formato Prometheus
- [ ] OpenAPI: `/docs` y `/redoc` deshabilitados en producción (`APP_ENV=production`)

### 11.2 Frontend (Vercel)

- [ ] Vercel: proyecto creado, `vercel --prod` ejecutado
- [ ] Vercel: dominio `talentup.es` y `www.talentup.es` añadidos y verificados
- [ ] Vercel: proxy `/api/*` → Railway funcionando (`curl https://talentup.es/api/health`)
- [ ] PWA: `manifest.json` y `sw_v2.js` devuelven 200
- [ ] HTTPS: certificado activo, redirección HTTP → HTTPS
- [ ] HSTS: cabecera `Strict-Transport-Security` presente
- [ ] Sin URLs `localhost` en el código del frontend

### 11.3 Frontend duplicado (GitHub Pages)

- [ ] GitHub Pages: source = GitHub Actions
- [ ] Workflow `deploy-frontend.yml` ejecutado correctamente
- [ ] URL `https://<usuario>.github.io/talentup-fichaje/` accesible

### 11.4 DNS y SSL

- [ ] DNS: `talentup.es` → A record a Vercel
- [ ] DNS: `www.talentup.es` → CNAME a `cname.vercel-dns.com`
- [ ] DNS: `api.talentup.es` → CNAME a Railway (si usa dominio custom)
- [ ] SSL: certificados válidos en frontend y backend
- [ ] HSTS: activo en ambos

### 11.5 Stripe

- [ ] Stripe: webhook endpoint configurado (`/api/billing/webhook`)
- [ ] Stripe: signing secret (`whsec_...`) en Railway
- [ ] Stripe: precios `STRIPE_PRICE_BASIC`, `STRIPE_PRICE_PRO`, `STRIPE_PRICE_KIT` configurados
- [ ] Stripe: eventos suscritos (`checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`, `customer.subscription.updated`)
- [ ] Flujo signup → checkout → login verificado end-to-end

### 11.6 CI/CD

- [ ] Railway: conectado a GitHub, auto-deploy en push a `master` (Root Directory = `backend`)
- [ ] Vercel: conectado a GitHub, auto-deploy en push (Root Directory = `frontend`)
- [ ] GitHub Actions: `backend-ci.yml` pasa (test-sqlite, test-postgres, build-and-push)
- [ ] Secret `RAILWAY_TOKEN` configurado en GitHub para `deploy-backend.yml`

### 11.7 Monitoring

- [ ] Uptime monitor sobre `https://talentup.es/api/health`
- [ ] Grafana: dashboard `talentup_overview` cargado
- [ ] Alertas configuradas (errores 5xx, latencia, DB/Redis caídos)
- [ ] Backup inicial de la base de datos

---

## 12. Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|----------------|---------|
| Backend no arranca: `REDIS_URL requerido en produccion` | Falta add-on Redis en Railway | `railway add` → Redis |
| Backend: `JWT_SECRET requerido en produccion` | Variable no configurada | `railway variables set JWT_SECRET="$(openssl rand -hex 32)"` |
| Backend: `PIN_HASH_SALT requerido` | Variable no configurada | `railway variables set PIN_HASH_SALT="$(openssl rand -hex 16)"` |
| `502 Bad Gateway` en Railway | Uvicorn no escucha en `$PORT` | Verifica `railway.json`: `startCommand` usa `--port $PORT` |
| Health check `503 degraded` | DB o Redis caídos | Revisa `db_status` y `redis_status` en el JSON del health check |
| CORS error en frontend | `CORS_ORIGINS` no incluye el dominio | `railway variables set CORS_ORIGINS="https://talentup.es,https://www.talentup.es"` |
| Migraciones fallan | Driver incorrecto en `DATABASE_URL` | Usa `postgresql+asyncpg://` para async |
| Stripe webhook 403 | `STRIPE_WEBHOOK_SECRET` desincronizado | Regenera signing secret en Stripe → actualiza en Railway |
| Stripe webhook 400 | Firma inválida o payload corrupto | Verifica que el endpoint URL coincide y el secret es correcto |
| PWA no instala | `manifest.json` o `sw_v2.js` devuelven 404 | Verifica `vercel.json` routes para estos paths |
| Login 401 en producción | `JWT_SECRET` cambiado | Los tokens existentes se invalidan; es esperado tras rotación |
| GitHub Pages: API no responde | Sin proxy dinámico en Pages | Usa Vercel como frontend principal; Pages es solo respaldo |
| ESP32 no conecta al backend | URL incorrecta o HTTP vs HTTPS | Verifica `BACKEND_URL` en `platformio.ini` build_flags |

---

**Mantenimiento:** revisa semanalmente los logs de Railway (`railway logs`), las métricas de Grafana y el health check. Escala los recursos de Railway cuando superes los límites del plan (CPU, RAM, ancho de banda). Mantén las dependencias actualizadas (`pip-audit` para Python, `npm audit` para Node).