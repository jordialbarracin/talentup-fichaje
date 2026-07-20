# TalentUP Fichaje — Guía Técnica para Desarrolladores

> Versión: 2.0.0 · Última actualización: julio 2026
> Repositorio: `D:/talentup-fichaje` · API base: `http://localhost:8000/api`

---

## 1. Arquitectura

### 1.1 Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.11 + FastAPI (async) |
| ORM | SQLAlchemy 2.0 async |
| Base de datos | PostgreSQL 16 (producción) / SQLite (desarrollo y tests) |
| Caché / colas / rate limiting | Redis 7 |
| Auth | JWT HS256 + bcrypt (passwords) + SHA-256 (PIN rápido) |
| Frontend web | SPA vanilla HTML/CSS/JS (`frontend/`) |
| Terminal física | HTML estática (`terminal/`, puerto 3001) |
| PWA móvil | HTML + Service Worker (`mobile/`) |
| Firmware hardware | ESP32 + PN532 NFC vía SPI (`hardware/esp32_fichaje/`) |
| Contenedores | Docker + Docker Compose |
| Hosting recomendado | Railway (backend) + Vercel/GitHub Pages (frontend) + Neon (PostgreSQL) |
| CI/CD | GitHub Actions |

### 1.2 Diagrama de componentes

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Navegador  │   │  Terminal   │   │  PWA móvil  │
│  :3000      │   │  :3001      │   │  /mobile/   │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │ HTTP / WebSocket
              ┌──────────▼──────────┐
              │   FastAPI backend     │
              │   :8000 /api          │
              │   JWT + CSP + logs    │
              └──────────┬────────────┘
                         │ asyncpg / aiosqlite
              ┌──────────▼──────────┐
              │   PostgreSQL / SQLite │
              └───────────────────────┘
                         │
              ┌──────────▼──────────┐
              │   Redis (rate limit, │
              │   health, sesiones)   │
              └───────────────────────┘
```

### 1.3 Estructura de carpetas

```
talentup-fichaje/
├── backend/
│   ├── app/
│   │   ├── main.py              # Punto de entrada FastAPI
│   │   ├── database.py          # Engine async + init_db
│   │   ├── auth.py              # JWT, bcrypt, PIN hash
│   │   ├── rate_limiter.py      # Rate limiting Redis/memoria
│   │   ├── logging_config.py    # Logs JSON
│   │   ├── models/              # 19 modelos SQLAlchemy
│   │   ├── routers/             # 21 routers de API
│   │   └── schema.sql           # Esquema de referencia PostgreSQL
│   ├── tests/                   # pytest (67 tests)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.json
├── frontend/                    # SPA web
├── terminal/                    # Interfaz terminal
├── mobile/                        # PWA
├── hardware/esp32_fichaje/      # Firmware ESP32
├── tests/e2e/                     # Playwright
├── docker-compose.yml
├── .env.example
└── .github/workflows/             # CI/CD
```

---

## 2. Instalación y puesta en marcha

### 2.1 Requisitos

- Python 3.11+
- Node.js 18+ (solo para Playwright)
- Git
- Docker + Docker Compose (opcional)
- Redis (opcional en dev, obligatorio en prod)

### 2.2 Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/talentup-fichaje.git
cd talentup-fichaje
```

### 2.3 Backend (desarrollo con SQLite)

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt

# Variables mínimas de entorno
set DATABASE_URL=sqlite+aiosqlite:///./talentup_fichaje.db
set PIN_HASH_SALT=dev-salt-16bytes
set JWT_SECRET=dev-secret-32bytes

# Arrancar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Accede a:

- API: `http://localhost:8000/api`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`

### 2.4 Docker Compose (PostgreSQL + Redis + backend)

```bash
# Desde la raíz del proyecto
cp .env.example .env
# Edita .env con valores reales, especialmente POSTGRES_PASSWORD, JWT_SECRET y PIN_HASH_SALT

docker compose up --build

# Ver logs
docker compose logs -f backend

# Parar
docker compose down
# Parar y borrar volúmenes
docker compose down -v
```

### 2.5 Frontend web

Sirve `frontend/index.html` con cualquier servidor estático:

```bash
cd frontend
python -m http.server 3000
# o
npx serve . -p 3000
```

### 2.6 Terminal

```bash
cd terminal
python -m http.server 3001
```

### 2.7 PWA móvil

Sirve la carpeta raíz del frontend para que `/mobile/` sea accesible:

```bash
cd frontend
python -m http.server 3000
# Accede en el móvil a http://localhost:3000/mobile/
```

---

## 3. Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores.

| Variable | Descripción | Ejemplo / Valor por defecto |
|----------|-------------|-----------------------------|
| `APP_ENV` | Entorno de ejecución | `development` · `staging` · `production` |
| `LOG_LEVEL` | Nivel de logging | `INFO` · `DEBUG` · `WARNING` · `ERROR` |
| `LOG_FORMAT` | Formato de logs | `json` o `auto` |
| `BACKEND_URL` | URL pública del backend | `http://localhost:8000` |
| `PORT` | Puerto del servidor | `8000` |
| `DATABASE_URL` | URL de la base de datos | `sqlite+aiosqlite:///./talentup_fichaje.db` (dev) · `postgresql+asyncpg://user:pass@host:5432/db` (prod) |
| `REDIS_URL` | URL de Redis | `redis://localhost:6379/0` |
| `JWT_SECRET` | Secreto para firmar JWT | Generar con `openssl rand -hex 32` |
| `JWT_EXPIRE_MINUTES` | Duración del access token | `480` (8 horas) |
| `PIN_HASH_SALT` | Sal para hash rápido de PIN (SHA-256) | Generar con `openssl rand -hex 16` |
| `CORS_ORIGINS` | Orígenes permitidos | `http://localhost:3000,http://localhost:3001` |
| `FRONTEND_URL` | URL pública del frontend | `http://localhost:3000` |
| `STRIPE_SECRET_KEY` | Clave secreta de Stripe | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Secreto del webhook de Stripe | `whsec_...` |
| `STRIPE_PRICE_BASIC` | ID de precio Basic | `price_basic_dev` |
| `STRIPE_PRICE_PRO` | ID de precio Pro | `price_pro_dev` |
| `POSTGRES_USER` | Usuario PostgreSQL (solo Docker Compose) | `talentup` |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL | Obligatoria en Docker |
| `POSTGRES_DB` | Nombre de la base de datos | `talentup_fichaje` |

### Comando para generar secretos

```bash
openssl rand -hex 32   # JWT_SECRET
openssl rand -hex 16   # PIN_HASH_SALT
```

---

## 4. API REST

Base URL: `http://localhost:8000/api`

Autenticación: JWT en cookie `access_token` httpOnly (preferente) o header `Authorization: Bearer <token>`.

### 4.1 Endpoints principales

| Método | Endpoint | Descripción | Rol mínimo |
|--------|----------|-------------|------------|
| `POST` | `/api/auth/login` | Login devuelve cookies httpOnly | Público |
| `POST` | `/api/auth/register` | Registro autogestionado (crea tenant) | Público |
| `POST` | `/api/auth/refresh` | Renueva access token desde cookie | Público (cookie) |
| `POST` | `/api/auth/logout` | Cierra sesión y limpia cookies | Autenticado |
| `GET` | `/api/auth/me` | Información del usuario actual | Autenticado |
| `GET` | `/api/employees` | Listar empleados (paginado) | owner |
| `GET` | `/api/employees/{id}` | Ver empleado | owner |
| `POST` | `/api/employees` | Crear empleado | owner |
| `PUT` | `/api/employees/{id}` | Actualizar empleado | owner |
| `DELETE` | `/api/employees/{id}` | Eliminar empleado | owner |
| `POST` | `/api/clock` | Fichaje por PIN | Público |
| `POST` | `/api/clock/nfc` | Fichaje por NFC | Público + device token |
| `POST` | `/api/clock/qr` | Fichaje por QR | Público |
| `GET` | `/api/clock/history` | Historial de fichajes | manager |
| `GET` | `/api/clock/today` | Fichajes de hoy | manager |
| `POST` | `/api/clock/{id}/cancel` | Anular fichaje | manager |
| `GET` | `/api/vacations` | Listar solicitudes | owner |
| `POST` | `/api/vacations` | Crear solicitud | owner |
| `POST` | `/api/vacations/{id}/approve` | Aprobar vacaciones | owner |
| `POST` | `/api/vacations/{id}/reject` | Rechazar vacaciones | owner |
| `GET` | `/api/reports/hours` | Horas trabajadas | manager |
| `GET` | `/api/reports/incidents` | Informe de incidencias | manager |
| `GET` | `/api/reports/export` | Exportar PDF/Excel | manager |
| `GET` | `/api/reports/inspection` | Informe para Inspección | manager |
| `POST` | `/api/devices` | Registrar dispositivo/terminal | manager |
| `GET` | `/api/health` | Health check profundo | Público |

> Swagger completo en `http://localhost:8000/docs` (deshabilitado en producción por seguridad).

### 4.2 Ejemplos curl

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@latagliatella.es","password":"owner123"}' \
  -c cookies.txt -b cookies.txt
```

#### Datos del usuario actual

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

#### Crear empleado

```bash
curl -X POST http://localhost:8000/api/employees \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "name": "Lucía Fernández",
    "dni": "12345678Z",
    "pin": "9876",
    "nfc_uid": "A1:B2:C3:D4",
    "clock_method": "pin",
    "horas_semanales": 40,
    "coste_hora": 12.50
  }'
```

#### Listar empleados

```bash
curl "http://localhost:8000/api/employees?page=1&limit=20" \
  -H "Authorization: Bearer <TOKEN>"
```

#### Actualizar empleado

```bash
curl -X PUT http://localhost:8000/api/employees/<EMPLOYEE_ID> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"phone":"+34600123456","is_active":true}'
```

#### Eliminar empleado

```bash
curl -X DELETE http://localhost:8000/api/employees/<EMPLOYEE_ID> \
  -H "Authorization: Bearer <TOKEN>"
```

#### Fichaje por PIN

```bash
curl -X POST http://localhost:8000/api/clock \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "<TENANT_ID>",
    "pin": "1234",
    "type": "auto"
  }'
```

#### Fichaje por NFC

```bash
curl -X POST http://localhost:8000/api/clock/nfc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <DEVICE_TOKEN>" \
  -d '{
    "tenant_id": "<TENANT_ID>",
    "nfc_uid": "04:A1:B2:C3:D4:E5"
  }'
```

#### Fichaje por QR

```bash
curl -X POST http://localhost:8000/api/clock/qr \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "<TENANT_ID>",
    "employee_id": "<EMPLOYEE_ID>"
  }'
```

#### Crear solicitud de vacaciones

```bash
curl -X POST http://localhost:8000/api/vacations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "employee_id": "<EMPLOYEE_ID>",
    "start_date": "2026-08-01",
    "end_date": "2026-08-10",
    "total_days": 8,
    "reason": "Vacaciones de verano"
  }'
```

#### Aprobar vacaciones

```bash
curl -X POST http://localhost:8000/api/vacations/<VACATION_ID>/approve \
  -H "Authorization: Bearer <TOKEN>"
```

#### Informe de horas

```bash
curl "http://localhost:8000/api/reports/hours?date_from=2026-07-01&date_to=2026-07-31" \
  -H "Authorization: Bearer <TOKEN>"
```

#### Exportar PDF

```bash
curl "http://localhost:8000/api/reports/export?format=pdf&date_from=2026-07-01&date_to=2026-07-31" \
  -H "Authorization: Bearer <TOKEN>" \
  --output fichajes_julio.pdf
```

#### Registrar dispositivo/terminal

```bash
curl -X POST http://localhost:8000/api/devices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "tenant_id": "<TENANT_ID>",
    "name": "Terminal entrada"
  }'
```

---

## 5. WebSocket /ws/nfc

El endpoint WebSocket expone eventos en tiempo real del lector NFC. Se usa en el panel de administración y en la terminal web.

### 5.1 Conexión

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/nfc');

ws.onopen = () => {
  console.log('Conectado al lector NFC');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Evento NFC:', data);
};

ws.onclose = () => {
  console.log('Desconectado del lector NFC');
};

// Ping para mantener viva la conexión
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);
```

### 5.2 Formato de eventos

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `nfc_connected` | Confirmación de conexión | `{"type":"nfc_connected","message":"Lector NFC conectado"}` |
| `nfc_read` | Tarjeta leída y fichaje registrado | `{"type":"nfc_read","uid":"04:A1:B2:C3:D4:E5","employee":"Carlos","action":"in","time":"14:32"}` |
| `nfc_disconnected` | Lector desconectado | `{"type":"nfc_disconnected","message":"Lector NFC desconectado"}` |
| `pong` | Respuesta a keep-alive | `{"type":"pong"}` |

### 5.3 Mensajes del cliente

- `ping`: el servidor responde con `{"type":"pong"}`.

---

## 6. Base de datos

### 6.1 Modelos SQLAlchemy (19 tablas)

Definidos en `backend/app/models/`:

1. `Tenant` — restaurantes / empresas
2. `User` — owner, manager, super_admin
3. `Employee` — trabajadores que fichan
4. `Shift` — turnos laborales
5. `Schedule` — asignación empleado-turno-fecha
6. `ClockIn` — registros de fichaje
7. `Incident` — incidencias auto-detectadas
8. `AuditLog` — trazabilidad de cambios
9. `Contract` — contratos de empleados
10. `Holiday` — festivos del tenant
11. `VacationRequest` — solicitudes de vacaciones
12. `Leave` — bajas y permisos
13. `Overtime` — horas extras
14. `Payroll` — nóminas
15. `Notification` — notificaciones
16. `WorkCalendar` — calendario laboral
17. `Geofence` — geocercas para fichaje
18. `DocumentTemplate` — plantillas de documentos
19. `Device` — terminales / dispositivos NFC

### 6.2 Relaciones principales

```
Tenant 1──∞ User
Tenant 1──∞ Employee
Tenant 1──∞ Shift
Tenant 1──∞ Schedule
Tenant 1──∞ ClockIn
Tenant 1──∞ Incident
Tenant 1──∞ AuditLog
Employee ── Shift
Employee 1──∞ Contract
Employee 1──∞ VacationRequest
Employee 1──∞ Leave
Employee 1──∞ ClockIn
User ── Cancelador de ClockIn (cancelled_by)
User ── Resolvedor de Incident (resolved_by)
```

### 6.3 Índices compuestos

Referencias en `backend/app/schema.sql` y modelos:

```sql
CREATE INDEX idx_clock_ins_tenant_date ON clock_ins(tenant_id, timestamp);
CREATE INDEX idx_clock_ins_employee ON clock_ins(employee_id, timestamp);
CREATE INDEX idx_employees_tenant ON employees(tenant_id);
CREATE INDEX idx_incidents_tenant_date ON incidents(tenant_id, date);
CREATE INDEX idx_schedules_tenant_date ON schedules(tenant_id, date);
```

El modelo `Employee` también usa `pin_hash_fast` (SHA-256) indexado para búsquedas rápidas de PIN antes de verificar con bcrypt.

### 6.4 Migraciones

- **Desarrollo (SQLite):** las tablas se crean automáticamente con `create_all()` en el `lifespan`.
- **Producción (PostgreSQL):** se ejecuta `alembic upgrade head` al arrancar.

```bash
cd backend
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```

### 6.5 RLS en PostgreSQL (recomendado para producción)

Para reforzar el aislamiento multi-tenant en PostgreSQL:

```sql
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE clock_ins ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_employees ON employees
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_clock_ins ON clock_ins
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

> Nota: RLS es una capa adicional de defensa; la aplicación ya filtra por `tenant_id` en todas las consultas.

### 6.6 Seed de desarrollo

El fixture de tests (`backend/tests/conftest.py`) crea datos de prueba con:

- Super admin: `admin@talentup.es` / `admin123`
- Owner Tenant A: `owner@latagliatella.es` / `owner123`
- Manager Tenant A: `manager@latagliatella.es` / `manager123`
- Empleados con PINs `1234` y `5678`.

---

## 7. Firmware ESP32

Ubicación: `hardware/esp32_fichaje/`

### 7.1 Materiales

- ESP32 NodeMCU-32S / DOIT
- Módulo PN532 NFC (SPI)
- 2 LEDs (verde/rojo) + resistencias 220 Ω
- Cables Dupont
- Fuente 5V USB

### 7.2 Conexiones ESP32 ↔ PN532

| ESP32 | PN532 |
|-------|-------|
| GPIO 5  | NSS (CS) |
| GPIO 18 | SCK |
| GPIO 19 | MISO |
| GPIO 23 | MOSI |
| 3.3V    | VCC |
| GND     | GND |

LEDs:

- GPIO 2 → LED verde
- GPIO 4 → LED rojo
- GPIO 15 → LED azul (cola offline)

### 7.3 Configuración previa

Edita las macros al inicio de `esp32_fichaje.ino`:

```cpp
#define WIFI_SSID     "TU_WIFI_SSID"
#define WIFI_PASS     "TU_WIFI_PASSWORD"
#define BACKEND_URL   "http://192.168.1.100:8000"
#define TENANT_ID     "TU_TENANT_ID"
#define DEVICE_TOKEN  "TU_DEVICE_TOKEN"
```

Para obtener un `DEVICE_TOKEN`, usa la API REST:

```bash
curl -X POST http://localhost:8000/api/devices \
  -H "Authorization: Bearer <OWNER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"<TENANT_ID>","name":"Terminal entrada"}'
```

### 7.4 Compilación y subida

#### Con PlatformIO (recomendado)

```bash
cd hardware/esp32_fichaje

# Compilar y subir
pio run -t upload

# Monitor serie
pio device monitor --baud 115200
```

#### Con Arduino IDE

1. Instala el soporte de placas ESP32.
2. Instala las librerías `Adafruit PN532` y `ArduinoJson`.
3. Selecciona tu placa y puerto.
4. Sube el sketch.

#### Con esptool.py

```bash
esptool.py --chip esp32 --port COM3 write_flash 0x1000 firmware.bin
```

### 7.5 Comportamiento del firmware

1. Se conecta al WiFi configurado.
2. Inicializa PN532 en modo lectura pasiva ISO 14443A.
3. Lee UID de tarjetas NFC.
4. Envía `POST /api/clock/nfc` con `nfc_uid` y `tenant_id`.
5. LED verde si el fichaje es correcto; rojo si hay error.
6. Si no hay conexión, guarda en cola offline con LittleFS y sincroniza cada 30 segundos.
7. Watchdog de 10 segundos para reinicio automático en caso de cuelgue.

---

## 8. Testing

### 8.1 Backend — pytest (67 tests)

```bash
cd backend
# SQLite en memoria por defecto
pytest

# Verbose con coverage
pytest -v --cov=app --cov-report=term-missing

# Tests de seguridad únicamente
pytest tests/test_security.py -v
```

Cobertura de tests:

- Auth: login, refresh, logout, cookies httpOnly
- Employees: CRUD + aislamiento entre tenants
- Clock: PIN, NFC, QR, rate limiting, bloqueo por PIN erróneo
- Vacaciones, bajas, festivos
- Reports: horas, incidencias, export PDF/Excel
- Seguridad: JWT, roles, CORS, CSP

### 8.2 Frontend — vitest

Si el frontend incluye tests unitarios con vitest:

```bash
cd frontend
npm install
npm run test        # o npx vitest
```

> Nota: en la estructura actual el frontend es vanilla HTML/JS; el package.json solo incluye Playwright. Si se añaden tests vitest en el futuro, el comando será `npx vitest`.

### 8.3 E2E — Playwright

```bash
# Instalar navegadores (primera vez)
npx playwright install chromium

# Desde la raíz del proyecto
cd D:/talentup-fichaje
npx playwright test

# Con UI para depuración
npx playwright test --ui

# Un test concreto
npx playwright test tests/e2e/test_login.spec.js
```

Requisitos previos para Playwright:

- Backend en `http://localhost:8000`
- Frontend en `http://localhost:3000`
- Terminal en `http://localhost:3001`
- PWA en `http://localhost:3000/mobile/`

---

## 9. Deploy

### 9.1 Docker Compose (local / staging)

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/api/health
```

### 9.2 Backend en Railway

1. Conecta el repositorio a Railway.
2. Railway detecta `backend/Dockerfile` y `railway.json`.
3. Configura variables de entorno:
   - `DATABASE_URL` (PostgreSQL)
   - `REDIS_URL`
   - `JWT_SECRET`
   - `PIN_HASH_SALT`
   - `CORS_ORIGINS` (URL del frontend)
   - `FRONTEND_URL`
4. Despliegue automático con GitHub Actions:

```yaml
# .github/workflows/deploy-backend.yml (ya incluido)
```

Requiere el secret `RAILWAY_TOKEN` en GitHub.

```bash
# Deploy manual con Railway CLI
railway login
railway up --service=talentup-backend --detach
railway run --service=talentup-backend alembic upgrade head
```

### 9.3 Frontend en Vercel

Configuración en `frontend/vercel.json`:

```json
{
  "version": 2,
  "builds": [{ "src": "index.html", "use": "@vercel/static" }],
  "routes": [
    { "src": "/api/(.*)", "dest": "https://talentup-fichaje-backend.railway.app/api/$1" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

Pasos:

1. Importa el repositorio en Vercel.
2. Root Directory: `frontend`
3. Build Command: vacío (estático)
4. Output Directory: `.`
5. Deploy.

### 9.4 GitHub Pages

Para el landing o documentación estática:

```bash
git checkout -b gh-pages
git add landing.html
git commit -m "Deploy GitHub Pages"
git push origin gh-pages
```

En GitHub → Settings → Pages, selecciona la rama `gh-pages` y la carpeta raíz.

### 9.5 CI/CD

El repositorio incluye `.github/workflows/deploy-backend.yml`:

- Se ejecuta en push a `main` o `master` cuando cambia `backend/**`.
- Instala Railway CLI.
- Hace `railway up` al servicio configurado.
- Ejecuta migraciones opcionales.

---

## 10. Seguridad

### 10.1 JWT en cookies httpOnly

`backend/app/routers/auth.py`:

```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=True,
    samesite="lax",
    max_age=28800,
)
```

- El token no viaja en el cuerpo JSON.
- El frontend lo envía automáticamente en peticiones con `credentials: include`.
- El endpoint `/api/auth/refresh` rota el refresh token y revoca el anterior.

### 10.2 CSP con nonce por petición

`backend/app/main.py`:

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.csp_nonce = secrets.token_urlsafe(16)
        response = await call_next(request)
        nonce = request.state.csp_nonce
        csp = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' cdn.jsdelivr.net; "
            f"style-src 'self' 'nonce-{nonce}'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if _is_production():
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
```

Las respuestas HTML deben inyectar `nonce="{{ nonce }}"` en etiquetas `<script>` y `<style>`.

### 10.3 Rate limiting con Redis

`backend/app/rate_limiter.py`:

- Límite general de fichajes: `10/minuto` por IP+tenant.
- PIN erróneos: `5/minuto` → bloqueo de `5 minutos`.
- Registro: `3/hora` por IP.
- En producción usa Redis; en dev usa memoria como fallback.

### 10.4 Hash de PIN

- Almacenamiento principal: `bcrypt` (`pin_hash`).
- Búsqueda rápida indexada: `SHA-256(pin + PIN_HASH_SALT)` (`pin_hash_fast`).
- Flujo: buscar por hash rápido → verificar con bcrypt.

```python
def compute_pin_hash_fast(pin: str) -> str:
    return hashlib.sha256((pin + _SECRET_SALT).encode("utf-8")).hexdigest()
```

### 10.5 Firma de webhooks de Stripe

`backend/app/routers/billing.py` verifica la firma del webhook:

```python
stripe_webhook_secret = os.environ["STRIPE_WEBHOOK_SECRET"]
event = stripe.Webhook.construct_event(payload, sig_header, stripe_webhook_secret)
```

- El payload crudo debe leerse antes de cualquier parseo JSON.
- Si la firma falla, se responde `400`.

### 10.6 Otras medidas

- Límite de tamaño de body: 1 MB.
- Escape de HTML en campos de texto libre.
- Roles y aislamiento por tenant en todas las rutas protegidas.
- Logs de auditoría (`audit_log`) para cambios en empleados, fichajes y vacaciones.

---

## 11. Monitoreo

### 11.1 Health check

`GET /api/health`

```bash
curl http://localhost:8000/api/health
```

Respuesta:

```json
{
  "status": "ok",
  "service": "TalentUP Fichaje API",
  "version": "2.0.0",
  "started_at": "2026-07-20T10:00:00Z",
  "uptime_seconds": 3600,
  "db_status": "ok",
  "redis_status": "ok"
}
```

En caso de fallo devuelve `503` con `status: degraded` y detalles del error.

### 11.2 Métricas Prometheus

`GET /api/metrics`

El endpoint expone métricas básicas en formato Prometheus. Ejemplo de scrap:

```bash
curl http://localhost:8000/api/metrics
```

Salida esperada:

```
# HELP talentup_uptime_seconds Uptime del servicio
# TYPE talentup_uptime_seconds gauge
talentup_uptime_seconds 3600

# HELP talentup_requests_total Total de peticiones
# TYPE talentup_requests_total counter
talentup_requests_total{method="GET",path="/api/health",status="200"} 42
```

> Nota: confirma en `backend/app/main.py` o en un router de métricas si `/api/metrics` está activo; en caso contrario añade un router `metrics.py` con `prometheus_client`.

### 11.3 Logging JSON

`backend/app/logging_config.py` configura `python-json-logger`. En producción los logs se emiten como JSON con campos estructurados:

```json
{
  "event": "request",
  "method": "POST",
  "path": "/api/clock",
  "status_code": 201,
  "duration_ms": 45.2,
  "request_id": "a1b2c3d4"
}
```

Variables relacionadas:

- `LOG_LEVEL=INFO`
- `LOG_FORMAT=json`

### 11.4 Docker healthcheck

El `Dockerfile` incluye:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT:-8000}/api/health || exit 1
```

### 11.5 Integración con Prometheus + Grafana (opcional)

```yaml
# scrape_config adicional en prometheus.yml
scrape_configs:
  - job_name: 'talentup-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics'
```

---

## 12. Comandos rápidos de referencia

```bash
# Backend
uvicorn app.main:app --reload --port 8000
cd backend && pytest -v

# Frontend / Terminal / PWA
cd frontend && python -m http.server 3000
cd terminal && python -m http.server 3001

# Docker
docker compose up --build
docker compose down -v

# Tests E2E
npx playwright test
npx playwright test --ui

# Firmware ESP32
cd hardware/esp32_fichaje
pio run -t upload
pio device monitor --baud 115200

# Secretos
openssl rand -hex 32   # JWT_SECRET
openssl rand -hex 16   # PIN_HASH_SALT
```

---

## 13. Notas y convenciones

- Todos los endpoints protegidos usan dependencias `require_owner`, `require_manager` o `require_super_admin`.
- Las fechas se intercambian en formato ISO 8601 (`YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SSZ`).
- La API es multi-tenant: cada tenant aísla sus empleados, fichajes, informes y configuración.
- En producción desactiva Swagger (`docs_url=None`) y fuerza HTTPS.
- Los fichajes son inmutables; para corregir se usa `/api/clock/{id}/cancel` y se registra el motivo.

---

**Documento generado para el equipo de desarrollo y operaciones de TalentUP Fichaje.**
