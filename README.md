# TalentUP Fichaje

**SaaS de fichaje digital para hostelería.**
Multi-tenant. Cumple el Real Decreto-ley 8/2019 de registro de jornada en España.

## Design System v4.3 — 10/10 Antigravity Approved

- Tipografia: Inter (UI) + Geist Mono (datos tabulares)
- Fondo: #F1F1EE (gris calido, no blanco)
- Acento marca: #FF6B35 (solo CTAs y 1-2 puntos foco)
- Acento highlight: #D4FF32 (neon, focus-visible, highlights puntuales)
- Glass: solo en 1 componente (estado fichado)
- 12 pictogramas custom SVG (no Lucide)
- Dark mode nativo con toggle
- WCAG AA con focus-visible neon
- 8pt grid, 4 breakpoints (kiosko/mobile/tablet/desktop)
- Microanimaciones: live-pulse, chart hover scale, terminal hover lift

[![CI](https://github.com/jordialbarracin/talentup-fichaje/actions/workflows/ci.yml/badge.svg)](https://github.com/jordialbarracin/talentup-fichaje/actions)

---

## Stack

| Capa | Tecnologia |
|------|-----------|
| **Frontend** | HTML + CSS + JavaScript vanilla (SPA), i18n ES/CA/EN |
| **Backend** | Python 3.11 / FastAPI (async) |
| **Base de datos** | PostgreSQL 16 (produccion), SQLite (local dev) |
| **Auth** | JWT con access + refresh tokens, bcrypt |
| **Seguridad** | Rate limiting, CORS, multi-tenant isolation, audit log |
| **Hardware** | ESP32 CYD 2432S028 + PN532 NFC (I2C) + TFT_eSPI |
| **Monitoring** | Grafana + PostgreSQL datasource |
| **CI/CD** | GitHub Actions (test + build) |
| **Hosting** | Vercel (frontend), Railway/Supabase (backend) |

---

## Caracteristicas

- **Fichaje NFC**: empleados fichan con tarjeta/llavero NFC
- **Fichaje PIN**: alternativa con PIN numerico
- **Multi-tenant**: cada empresa ve solo sus datos
- **Turnos y horarios**: gestion completa de turnos, tolerancia, descansos
- **Incidencias**: deteccion automatica de retrasos, ausencias, salidas anticipadas
- **Vacaciones y permisos**: solicitud, aprobacion, rechazo
- **Horas extra**: calculo automatico, compensacion, pago
- **Nomminas**: cierre mensual, calculo de horas trabajadas
- **Contratos**: gestion de tipos de contrato, renovaciones, duracion
- **Calendario laboral**: generacion automatica de calendario anual con festivos
- **Notificaciones**: sistema in-app con prioridades y categorias
- **Reportes**: exportacion PDF y Excel, horas trabajadas, incidencias
- **i18n**: Espanol, Catalan, Ingles
- **RGPD**: politica de privacidad y DPA incluidos
- **OTA**: actualizacion del firmware remoto
- **Offline queue**: fichajes guardados sin WiFi, enviados al recuperar conexion

---

## Desarrollo Local

### Requisitos

- Python 3.11+
- Node.js (opcional, para servir el frontend)
- PlatformIO (para compilar firmware)

### 1. Clonar el repositorio

```bash
git clone https://github.com/jordialbarracin/talentup-fichaje.git
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

La API estara en `http://localhost:8000`.
Documentacion interactiva: `http://localhost:8000/docs`

### 3. Frontend

Abre `frontend/index.html` en tu navegador o sirve con un servidor estatico:

```bash
cd frontend
python -m http.server 3000
```

### 4. Variables de Entorno

Copia `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `JWT_SECRET` | Secreto para firmar tokens JWT | `openssl rand -hex 32` |
| `DATABASE_URL` | URL de conexion a PostgreSQL | `postgresql://user:***@host:5432/talentup_fichaje` |
| `CORS_ORIGINS` | Origienes permitidos | `http://localhost:3000,http://localhost:3001` |
| `PORT` | Puerto del servidor | `8000` |

### 5. Docker (opcional)

```bash
docker compose up --build
```

Esto levanta:
- PostgreSQL en puerto 5432
- Backend en puerto 8000
- Grafana en puerto 3001 (admin/talentup)

### 6. Firmware (ESP32 CYD)

```bash
cd hardware/esp32_fichaje_cyd
pio run -t upload --upload-port COM4
pio device monitor
```

---

## Tests

```bash
cd backend
python -m pytest -v
```

---

## Estructura del Proyecto

```
talentup-fichaje/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── auth.py              # JWT + refresh tokens
│   │   ├── audit.py             # Audit logging
│   │   ├── rate_limit.py        # Rate limiting middleware
│   │   ├── incidents.py         # Incident detection
│   │   ├── seed.py              # Seed data
│   │   ├── models/              # SQLAlchemy models
│   │   └── routers/             # API endpoints (16 routers)
│   ├── tests/                   # pytest tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html               # SPA + i18n
│   ├── i18n.js                  # Translation system ES/CA/EN
│   ├── landing.html             # Landing page
│   └── vercel.json
├── hardware/
│   ├── esp32_fichaje_cyd/       # CYD 2432S028 firmware (TFT_eSPI + PN532 I2C)
│   └── esp32_fichaje/           # ESP32 standalone firmware (SPI)
├── grafana/                     # Grafana dashboards + provisioning
├── .github/workflows/ci.yml     # GitHub Actions CI
├── docker-compose.yml           # PostgreSQL + Backend + Grafana
├── PRIVACY.md                   # RGPD privacy policy
├── DPA.md                       # Data Processing Agreement
└── README.md
```

---

## API Endpoints

| Router | Endpoints | Auth |
|--------|-----------|------|
| auth | login, register, me, refresh | - / super_admin |
| employees | CRUD + NFC assign | owner+ |
| clock | PIN, NFC, toggle in/out | - / owner+ |
| shifts | CRUD | owner+ |
| schedules | CRUD + date filtering | owner+ |
| tenants | CRUD | super_admin |
| contracts | CRUD | owner+ |
| holidays | CRUD | owner+ |
| vacations | list, create, approve, reject | owner+ |
| leave | CRUD | owner+ |
| overtime | list, create, calculate | owner+ |
| payroll | list, get, close | owner+ |
| notifications | list, create, unread, read | owner+ |
| calendar | get, generate | owner+ |
| reports | hours, incidents, PDF, Excel | owner+ |
| incidents | detect | owner+ |

---

## Licencia

Uso interno. Todos los derechos reservados.