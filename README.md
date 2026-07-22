# TalentUP Fichaje 🕐

**SaaS de fichaje digital para hostelería.**  
Multi-tenant. Cumple el Real Decreto-ley 8/2019 de registro de jornada en España.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| **Frontend** | HTML + CSS + JavaScript vanilla (SPA) |
| **Backend** | Python 3.11 / FastAPI (async) |
| **Base de datos** | PostgreSQL 16 (Neon en producción, SQLite en local) |
| **Auth** | JWT con bcrypt |
| **Hosting frontend** | Vercel |
| **Hosting backend** | Railway |
| **Hosting DB** | Neon (PostgreSQL serverless) |

---

## Desarrollo Local

### Requisitos

- Python 3.11+
- Node.js (opcional, para servir el frontend)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/talentup-fichaje.git
cd talentup-fichaje
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

La API estará en `http://localhost:8000`.  
Documentación interactiva: `http://localhost:8000/docs`

### 3. Frontend

Abre `frontend/index.html` en tu navegador o sirve con cualquier servidor estático:

```bash
cd frontend
python -m http.server 3000
# o con npx: npx serve .
```

### 4. Variables de Entorno

Copia `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `JWT_SECRET` | Secreto para firmar tokens JWT | `openssl rand -hex 32` |
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:pass@host:5432/talentup_fichaje` |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) | `http://localhost:3000,http://localhost:3001` |
| `PORT` | Puerto del servidor | `8000` |

### 5. Docker (opcional)

```bash
docker compose up --build
```

---

## Deploy

### Frontend → Vercel

1. Conecta tu repositorio de GitHub a Vercel.
2. Configura:
   - **Root Directory:** `frontend`
   - **Build Command:** (ninguno, es estático)
   - **Output Directory:** `.`
3. Vercel detectará automáticamente `vercel.json` y configurará las rutas SPA.
4. El `vercel.json` incluye un proxy para `/api/*` → Railway.

### Backend → Railway

1. Conecta tu repositorio a Railway.
2. Railway detectará el `Dockerfile` en `backend/` automáticamente.
3. Configura las variables de entorno en Railway:
   - `JWT_SECRET` — genera uno con `openssl rand -hex 32`
   - `DATABASE_URL` — la URL de tu base de datos en Neon
   - `CORS_ORIGINS` — la URL de tu frontend en Vercel
   - `PORT` — `8000`
4. Railway expondrá el servicio en `https://talentup-fichaje-backend.railway.app`.

### Base de Datos → Neon

1. Crea una cuenta en [neon.tech](https://neon.tech).
2. Crea un proyecto (región EU).
3. Copia la `DATABASE_URL` de conexión (formato `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb`).
4. Pégala en las variables de entorno de Railway.

---

## Comandos Útiles

```bash
# Backend
uvicorn app.main:app --reload          # Desarrollo con recarga automática
uvicorn app.main:app --host 0.0.0.0    # Producción local

# Tests
cd backend && python -m pytest tests/ -v

# Docker
docker compose up --build              # Levantar todo
docker compose down                    # Parar todo
docker compose down -v                 # Parar y borrar volúmenes

# Git
git add . && git commit -m "mensaje"   # Commit
git push origin main                   # Subir cambios
```

---

## Estructura del Proyecto

```
talentup-fichaje/
├── backend/
│   ├── app/
│   │   ├── main.py           # Punto de entrada FastAPI
│   │   ├── database.py       # Conexión a BD (async SQLAlchemy)
│   │   ├── auth.py           # Autenticación JWT
│   │   ├── audit.py          # Registro de auditoría
│   │   ├── seed.py           # Datos de prueba
│   │   ├── incidents.py      # Gestión de incidencias
│   │   ├── models/           # Modelos SQLAlchemy
│   │   ├── routers/          # Endpoints de la API
│   │   └── schema.sql        # Esquema SQL de referencia
│   ├── tests/                # Tests con pytest
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html            # SPA completa
│   └── vercel.json           # Configuración Vercel
├── terminal/
│   └── index.html            # Terminal web (admin)
├── docker-compose.yml        # Entorno local con PostgreSQL
├── .env.example              # Plantilla de variables de entorno
├── PRIVACY.md                # Política de privacidad RGPD
└── README.md
```

---

## Tests

### Backend (pytest)
```bash
cd backend
DATABASE_URL=sqlite+aiosqlite:// PIN_HASH_SALT=test-salt JWT_SECRET=test-secret python -m pytest --tb=no -q
```
**67 tests** — cubren auth, empleados, fichajes, vacaciones, bajas, reportes, seguridad (XSS, SQLi, JWT, CORS, rate limiting, WebSocket, Stripe webhook).

### Frontend (vitest)
```bash
cd frontend
npx vitest run
```
**28 tests** — JWT helpers, cookie helper, api helper, navegación, empleados, turnos, dashboard, modal, auth flow.

### E2E (Playwright)
```bash
# 1. Sembrar la BD de prueba (crea owner@latagliatella.es / owner123)
cd backend
DATABASE_URL=sqlite+aiosqlite:///./talentup_fichaje.db PIN_HASH_SALT=test-salt JWT_SECRET=test-secret venv/Scripts/python -m app.seed

# 2. Correr E2E (Playwright arranca backend en :8080 y frontend en :3000)
cd ../frontend
npx playwright test --reporter=line
```
**5 tests** — landing, login, dashboard, crear empleado, logout.

### Login de prueba
- Email: `owner@latagliatella.es`
- Contraseña: `owner123`

---

## Licencia

Uso interno. Todos los derechos reservados.
