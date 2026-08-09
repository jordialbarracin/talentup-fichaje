# DEPLOY — TalentUP Fichaje

**Versión:** 1.0.0 · **Fecha:** 09 Aug 2026 · **Stack:** Frontend → Vercel · Backend → Railway · DB → Supabase

> Guía paso a paso para desplegar TalentUP Fichaje en producción. El frontend SPA (HTML/JS vanilla + PWA) se publica en Vercel (`talentup.es`), el backend FastAPI en Railway (`talentup-fichaje-backend.railway.app`), y la base de datos PostgreSQL en Supabase.

---

## 0. Arquitectura de despliegue

```
┌──────────────────┐   HTTPS    ┌──────────────────┐   TCP 5432  ┌──────────────┐
│   Vercel (CDN)   │ ─────────> │  Railway (API)   │ ─────────> │   Supabase   │
│  talentup.es     │  /api/*     │  FastAPI+Uvicorn │            │  PostgreSQL  │
│  SPA + PWA       │  proxy      │  /api/health     │            │  + RLS       │
└──────────────────┘             └──────────────────┘            └──────────────┘
                                        │
                                        │  TCP 6379
                                        v
                                 ┌──────────────┐
                                 │    Redis      │
                                 │ (Railway add- │
                                 │  on o Upstash)│
                                 └──────────────┘
```

**Componentes:**

| Capa | Servicio | Recurso | URL |
|------|----------|---------|-----|
| Frontend | Vercel | Static + PWA | `https://talentup.es` |
| Backend | Railway | Docker (Python 3.11) | `https://talentup-fichaje-backend.railway.app` |
| Base de datos | Supabase | PostgreSQL 16 + RLS | `db.xxx.supabase.co:5432` |
| Cache/Colas | Railway Redis | Redis 7 | interno Railway |

**Prerrequisitos locales:**

```bash
node --version    # >= 18
python --version  # >= 3.11
git --version
# Cuentas con acceso:
#   - vercel.com  (login con GitHub)
#   - railway.app (login con GitHub)
#   - supabase.com (login con GitHub)
```

---

## 1. Preparar la base de datos — Supabase

### 1.1 Crear proyecto Supabase

1. Ve a https://supabase.com → **New Project**.
2. **Name:** `talentup-fichaje-prod`
3. **Database password:** genera una segura y guárdala:
   ```bash
   openssl rand -base64 24
   ```
4. **Region:** `Frankfurt (eu-central-1)` (más cercana a España para latencia baja).
5. **Plan:** Free para staging, Pro ($25/mes) para producción.
6. Espera ~2 min a que el proyecto se aprovisione.

### 1.2 Obtener la connection string

En el dashboard de Supabase → **Project Settings → Database → Connection string → URI**:

```
postgresql://postgres.[ref]:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```

> **Importante:** usa el **pooler** (puerto `6543`) para el backend. El puerto `5432` es para migraciones directas.

Guarda la URL completa en un gestor de secretos (1Password, Bitwarden). La usaremos como `DATABASE_URL` en Railway.

### 1.3 Aplicar migraciones (Alembic)

Las migraciones viven en `backend/alembic/versions/` y deben ejecutarse contra Supabase. Desde tu máquina local:

```bash
cd /c/Users/jordi/talentup-fichaje/backend

# 1. Instalar dependencias en un venv temporal
python -m venv .venv-deploy
source .venv-deploy/bin/activate    # Linux/Mac
# .venv-deploy\Scripts\activate      # Windows PowerShell
pip install -r requirements.txt

# 2. Apuntar Alembic a Supabase (puerto 5432, sin pooler, para DDL)
export DATABASE_URL="postgresql+asyncpg://postgres.[ref]:[PASSWORD]@aws-0-[region].pooler.supabase.com:5432/postgres"

# 3. Ejecutar migraciones
python -m alembic upgrade head

# 4. Verificar
python -m alembic current
# Debe mostrar: a15b29a48457 (head)
```

> Las migraciones incluyen: esquema inicial (`9b16fa110308`), índices compuestos (`1a2b3c4d5e6f`), merge heads (`4af19aaef1cc`) y RLS multi-tenant (`a15b29a48457`).

### 1.4 Verificar RLS (Row Level Security)

Supabase expone RLS en el panel → **Authentication → Policies**. Las migraciones de TalentUP ya crean las políticas de aislamiento por `tenant_id`. Verifica:

```bash
# Conéctate al SQL Editor de Supabase y ejecuta:
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND rowsecurity = true;
```

Debe devolver todas las tablas de negocio (employees, clock_events, incidents, etc.) con `rowsecurity = true`.

### 1.5 Sembrar datos iniciales (opcional, solo staging)

```bash
cd /c/Users/jordi/talentup-fichaje/backend
export DATABASE_URL="postgresql+asyncpg://postgres.[ref]:[PASSWORD]@aws-0-[region].pooler.supabase.com:5432/postgres"
python -m app.seed --env staging
```

> **Producción:** NO siembres datos de prueba. El primer tenant se crea vía signup self-serve.

---

## 2. Desplegar el backend — Railway

### 2.1 Crear proyecto en Railway

```bash
# Instalar CLI de Railway
npm install -g @railway/cli
railway login    # abre navegador para OAuth

cd /c/Users/jordi/talentup-fichaje/backend
railway init     # crea nuevo proyecto "talentup-fichaje"
```

### 2.2 Configurar variables de entorno

Railway detecta automáticamente `railway.json` (builder Docker, healthcheck `/api/health`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).

Configura las variables en el dashboard o por CLI:

```bash
# Obligatorias
railway variables set APP_ENV=production
railway variables set DATABASE_URL="postgresql+asyncpg://postgres.[ref]:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres"
railway variables set JWT_SECRET="$(openssl rand -hex 32)"
railway variables set PIN_HASH_SALT="$(openssl rand -hex 16)"
railway variables set CORS_ORIGINS="https://talentup.es,https://www.talentup.es"
railway variables set FRONTEND_URL="https://talentup.es"

# Redis (añadir como add-on en Railway)
railway add      # selecciona "Redis" → se inyecta REDIS_URL automáticamente

# Stripe (modo live para producción)
railway variables set STRIPE_SECRET_KEY="sk_live_..."
railway variables set STRIPE_WEBHOOK_SECRET="whsec_..."
railway variables set STRIPE_PRICE_BASIC="price_..."
railway variables set STRIPE_PRICE_PRO="price_..."

# Observabilidad
railway variables set LOG_LEVEL=INFO
railway variables set LOG_FORMAT=json
```

### 2.3 Desplegar

```bash
railway up      # construye la imagen Docker y despliega
```

Railway construirá el `Dockerfile` (multi-stage: builder + runtime, usuario non-root `talentup`, healthcheck a `/api/health`). El despliegue tarda ~3-5 min.

### 2.4 Verificar el backend

```bash
# Railway asigna una URL pública automáticamente:
# https://talentup-fichaje-backend.railway.app

curl https://talentup-fichaje-backend.railway.app/api/health
# Esperado: {"status":"healthy","version":"1.0.0",...}

# Verificar que las rutas responden
curl https://talentup-fichaje-backend.railway.app/api/auth/login \
  -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin@talentup.es","password":"test"}'
```

> Si el healthcheck falla, revisa los logs: `railway logs`. El error más común es `REDIS_URL requerido en produccion` — añade el add-on Redis.

### 2.5 Configurar dominio personalizado (opcional)

Railway → **Settings → Networking → Generate Domain** ya da una URL `.railway.app`. Para un dominio propio:

1. Railway → Settings → Networking → **Custom Domain** → `api.talentup.es`.
2. Añade el CNAME en tu DNS (Cloudflare, Namecheap, etc.) apuntando a `railway.app`.

---

## 3. Desplegar el frontend — Vercel

### 3.1 Instalar CLI y login

```bash
npm install -g vercel
vercel login    # abre navegador para OAuth con GitHub
```

### 3.2 Desplegar desde el directorio frontend

El `frontend/vercel.json` ya está configurado con:

- **Domains:** `talentup.es`, `www.talentup.es`
- **Redirects:** `landing.html` y `landing_new.html` → `/`
- **Builds:** `index.html` y `public/**` como static
- **Routes:** `/api/*` → proxy a `https://talentup-fichaje-backend.railway.app/api/$1`
- **Headers de seguridad:** `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `X-Robots-Tag`

```bash
cd /c/Users/jordi/talentup-fichaje/frontend

# Despliegue de preview (primera vez)
vercel          # responde: Link to existing project? No → "talentup-fichaje"

# Despliegue a producción
vercel --prod
```

### 3.3 Configurar dominio `talentup.es`

1. Vercel dashboard → **talentup-fichaje → Settings → Domains**.
2. **Add:** `talentup.es` y `www.talentup.es`.
3. En tu proveedor DNS, añade:
   ```
   talentup.es        A     76.76.21.21
   www.talentup.es    CNAME cname.vercel-dns.com
   ```
4. Espera a que Vercel valide el DNS (verde en el dashboard, ~5 min).

### 3.4 Variables de entorno del frontend

El frontend es estático pero `i18n.js` y `sw.js` pueden referenciar la URL del API. Verifica que en el código no haya URLs hardcodeadas a `localhost`:

```bash
cd /c/Users/jordi/talentup-fichaje/frontend
grep -rn "localhost" index.html i18n.js sw.js sw_v2.js
# Si hay resultados, reemplaza por https://talentup-fichaje-backend.railway.app
# o usa el proxy /api/ de Vercel (recomendado)
```

> **Recomendado:** el frontend siempre llama a `/api/...` (relativo). El `vercel.json` ya hace el proxy a Railway, evitando problemas de CORS y hardcoding.

### 3.5 Verificar el frontend

```bash
curl -I https://talentup.es
# Esperado: 200, headers de seguridad presentes

curl https://talentup.es/manifest.json | jq .name
# "TalentUP Fichaje"

# Verificar proxy API
curl https://talentup.es/api/health
# Debe devolver el mismo JSON que Railway directamente
```

---

## 4. Configuración de Stripe (webhooks)

Para que los pagos funcionen end-to-end en producción:

1. **Stripe Dashboard → Developers → Webhooks → Add endpoint.**
2. **Endpoint URL:** `https://talentup-fichaje-backend.railway.app/api/billing/webhook`
3. **Events:** `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`.
4. Copia el **Signing secret** (`whsec_...`) y actualízalo en Railway:
   ```bash
   railway variables set STRIPE_WEBHOOK_SECRET="whsec_nuevo_valor"
   railway redeploy
   ```
5. Crea los productos y precios en Stripe → copia los `price_id` → actualiza `STRIPE_PRICE_BASIC` y `STRIPE_PRICE_PRO` en Railway.

---

## 5. Verificación end-to-end

Checklist final antes de abrir al público:

```bash
# 1. Health check backend
curl https://talentup-fichaje-backend.railway.app/api/health | jq .status
# → "healthy"

# 2. Frontend carga
curl -o /dev/null -w "%{http_code}" https://talentup.es
# → 200

# 3. Proxy API funciona
curl https://talentup.es/api/health | jq .status
# → "healthy"

# 4. PWA manifest accesible
curl -o /dev/null -w "%{http_code}" https://talentup.es/manifest.json
# → 200

# 5. Service worker accesible
curl -o /dev/null -w "%{http_code}" https://talentup.es/sw_v2.js
# → 200

# 6. Signup self-serve (flujo completo)
#    Navega a https://talentup.es → Pricing → Subscribe →
#    completa checkout Stripe → verifica tenant creado en Supabase:
#    SELECT id, name, plan FROM tenants ORDER BY created_at DESC LIMIT 1;

# 7. Login backend con credenciales del tenant creado
curl -X POST https://talentup.es/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@restaurante.es","password":"..."}'
# → 200 + JWT token
```

---

## 6. CI/CD y rollbacks

### 6.1 Pipeline CI (GitHub Actions)

El repo ya incluye `.github/workflows/`. El flujo esperado:

1. **Push a `master`** → Railway despliega backend automáticamente (si está conectado al repo).
2. **Push a `master`** → Vercel despliega frontend automáticamente (si está conectado al repo).

Conecta ambos servicios a GitHub:

```bash
# Railway: Settings → Source Repo → conectar GitHub → seleccionar talentup-fichaje
#          → Root Directory = backend → Deploy on push = ON

# Vercel: Settings → Git → conectar GitHub → seleccionar talentup-fichaje
#         → Root Directory = frontend → Auto-deploy on push = ON
```

### 6.2 Rollback

**Railway:**
```bash
railway rollback   # lista deployments, selecciona el anterior
```

**Vercel:**
```bash
vercel ls                    # lista deployments
vercel promote <deployment-url>  # promueve un deploy anterior a producción
```

---

## 7. Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| Backend no arranca: `REDIS_URL requerido` | Falta add-on Redis en Railway | `railway add` → Redis |
| Backend: `DATABASE_URL requerido` | Variable no configurada | `railway variables set DATABASE_URL=...` |
| `502 Bad Gateway` en Railway | Uvicorn no escucha en `$PORT` | Verifica `railway.json`: `startCommand` usa `--port $PORT` |
| CORS error en frontend | `CORS_ORIGINS` no incluye el dominio | `railway variables set CORS_ORIGINS="https://talentup.es,https://www.talentup.es"` |
| Migraciones fallan en Supabase | Usando pooler (6543) para DDL | Usa puerto `5432` para `alembic upgrade` |
| Stripe webhook 400 | `STRIPE_WEBHOOK_SECRET` desincronizado | Regenera signing secret en Stripe → actualiza en Railway |
| PWA no instala | `manifest.json` o `sw_v2.js` devuelven 404 | Verifica `vercel.json` routes para estos paths |
| Login 401 en producción | `JWT_SECRET` cambiado sin re-login | Los tokens existentes se invalidan; es esperado tras rotación |

---

## 8. Checklist de go-live

- [ ] Supabase: proyecto creado, migraciones aplicadas, RLS verificado
- [ ] Railway: backend desplegado, health check verde, Redis conectado
- [ ] Railway: todas las variables de entorno configuradas (DB, JWT, CORS, Stripe)
- [ ] Vercel: frontend desplegado, dominio `talentup.es` activo
- [ ] Vercel: proxy `/api/*` → Railway funcionando
- [ ] Stripe: webhook endpoint configurado, signing secret en Railway
- [ ] Stripe: precios `STRIPE_PRICE_BASIC` y `STRIPE_PRICE_PRO` configurados
- [ ] Flujo signup → checkout → login verificado end-to-end
- [ ] DNS: `talentup.es` y `www.talentup.es` apuntando a Vercel
- [ ] DNS: `api.talentup.es` apuntando a Railway (si se usa dominio custom)
- [ ] CI/CD: Railway y Vercel conectados a GitHub, auto-deploy ON
- [ ] Backup inicial de Supabase (Settings → Database → Backups)

---

**Mantenimiento:** revisa semanalmente los logs de Railway (`railway logs`) y el panel de Supabase (uso de CPU/RAM). Los planes Free tienen límites — escala a Pro cuando superes 500 MB de DB o 10k requests/día en Railway.