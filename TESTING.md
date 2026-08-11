# Guía de Testing — TalentUP Fichaje

> **Repo:** [github.com/jordialbarracin/talentup-fichaje](https://github.com/jordialbarracin/talentup-fichaje)
> **Documentación relacionada:** [`CONTRIBUTING.md`](./CONTRIBUTING.md), [`ROADMAP.md`](./ROADMAP.md), [`DEPLOY.md`](./DEPLOY.md)

Esta guía describe **cómo se testea TalentUP Fichaje** en sus tres capas
(backend FastAPI, frontend SPA y firmware ESP32), cómo ejecutar cada suite de
tests localmente, cómo se integra el testing en CI/CD y cómo añadir tests nuevos
a cada suite. Es la referencia operativa para cualquier persona contribuidora
que vaya a escribir o ejecutar tests.

---

## Tabla de contenidos

1. [Visión general del testing](#1-visión-general-del-testing)
2. [Requisitos previos](#2-requisitos-previos)
3. [Backend — pytest](#3-backend--pytest)
4. [Backend — Migración de SQLite a PostgreSQL](#4-backend--migración-de-sqlite-a-postgresql)
5. [Frontend — vitest (unitarios)](#5-frontend--vitest-unitarios)
6. [Frontend — Playwright (e2e)](#6-frontend--playwright-e2e)
7. [Firmware — PlatformIO y pytest](#7-firmware--platformio-y-pytest)
8. [CI/CD — GitHub Actions](#8-cicd--github-actions)
9. [Cómo ejecutar todo localmente](#9-cómo-ejecutar-todo-localmente)
10. [Cómo añadir nuevos tests](#10-cómo-añadir-nuevos-tests)
11. [Cobertura y métricas](#11-cobertura-y-métricas)
12. [Solución de problemas](#12-solución-de-problemas)
13. [Apéndice: referencia de fixtures](#13-apéndice-referencia-de-fixtures)

---

## 1. Visión general del testing

TalentUP Fichaje tiene **tres suites de tests independientes**, una por capa
del proyecto, más un pipeline de CI/CD en GitHub Actions que las ejecuta de
forma automática en cada push y pull request.

| Capa | Framework | Dónde vive | Tests actuales | Entorno |
|------|-----------|------------|----------------|---------|
| **Backend** | pytest + pytest-asyncio + httpx | `backend/tests/` | 64 tests (121 en `test_api.py` + 16 en `test_security.py`, algunos parametrizados) | SQLite en memoria (por defecto) y PostgreSQL (CI) |
| **Frontend (unit)** | vitest + jsdom | `frontend/tests/` | 1 suite (`app.test.js`, 373 líneas) | jsdom, sin DOM real |
| **Frontend (e2e)** | Playwright | `frontend/e2e/` | 1 spec (`talentup.spec.cjs`) | Chromium headless contra backend + frontend reales |
| **Firmware** | pytest + mocks Python | `hardware/esp32_fichaje_cyd/test/` | 1 suite (`test_firmware.py`) | Python puro, sin hardware real |
| **CI/CD** | GitHub Actions | `.github/workflows/` | 4 workflows | Ubuntu runner |

### 1.1 Filosofía de testing

1. **Tests de aislamiento multi-tenant antes que nada**: el núcleo de
   TalentUP Fichaje es que un tenant no puede ver los datos de otro. Toda
   funcionalidad que toque datos de tenant debe tener tests que verifiquen
   este aislamiento.
2. **Tests en SQLite para velocidad, en PostgreSQL para fidelidad**: el
   desarrollo local usa SQLite en memoria (rápido, sin infraestructura). El
   CI ejecuta ambos: SQLite para feedback inmediato y PostgreSQL para
   detectar incompatibilidades de dialecto.
3. **Tests de frontend sin build**: la SPA es vanilla JS y no tiene paso de
   build. Los tests unitarios importan directamente `src/app.js` en jsdom.
4. **Tests de firmware sin hardware**: el firmware ESP32 se porta a Python
   con mocks y se testea con pytest. No se requiere un dispositivo físico
   para validar la lógica de fichaje, solo para tests de integración manual.
5. **Cobertura creciente, no perfecta**: no se exige el 100%, pero los PRs
   que añaden lógica de negocio deben mantener o subir la cobertura.

### 1.2 Números actuales

- **Backend**: 64 tests contabilizados (121 funciones `test_` en `test_api.py`
  + 16 en `test_security.py`, varias con parametrización que generan más
  casos). Solo corren en SQLite en local por defecto; PostgreSQL se ejecuta
  en CI.
- **Frontend unitario**: 1 suite con múltiples bloques `describe` que cubren
  `state`, `api`, `navigate`, `filterEmpleados`, `renderEmpleadosPage`,
  `loadEmpleados`, `loadTurnos`, `loadDashboard`, `showToast`, `openModal`,
  `closeModal`, `saveModal`, `enterApp`, `logout`, `getInitialToken`,
  `isTokenExpired`, `decodeJwt`, `updateOnlineStatus`, `updateDemoBanner`,
  `filterFichajes`, `filterVacaciones`, `filterBajas`.
- **Frontend e2e**: 1 spec Playwright con tests de landing, login, dashboard
  y navegación.
- **Firmware**: 1 suite Python con mocks de WiFi, TFT_eSPI, PN532, SPIFFS,
  HTTPClient, ArduinoOTA y watchdog.

---

## 2. Requisitos previos

Asegúrate de tener instalado lo siguiente antes de ejecutar cualquier suite:

```bash
# Python 3.11+ (backend y firmware)
python --version          # >= 3.11

# Node 18+ (frontend)
node --version            # >= 18

# git (clonar el repo)
git --version

# PlatformIO Core (solo si vas a compilar firmware, no para tests Python)
pio --version             # >= 6.1 (opcional)

# Docker y docker-compose (solo para tests de PostgreSQL locales)
docker --version          # >= 24 (opcional)
docker compose version
```

### 2.1 Dependencias de test por capa

| Capa | Instalación |
|------|-------------|
| Backend | `pip install pytest pytest-asyncio pytest-cov httpx` (además de `backend/requirements.txt`) |
| Frontend (unit) | `cd frontend && npm install` (vitest, jsdom) |
| Frontend (e2e) | `cd frontend && npm install && npx playwright install chromium` |
| Firmware | `pip install pytest` (no requiere PlatformIO para los tests Python) |

---

## 3. Backend — pytest

El backend usa **pytest** con **pytest-asyncio** (modo `auto`) y **httpx**
como cliente HTTP asíncrono para testear los endpoints de FastAPI sin levantar
un servidor real.

### 3.1 Estructura de tests del backend

```
backend/
├── pytest.ini                      # Configuración: asyncio_mode = auto
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures compartidas (client, seed_data, db_session)
│   ├── test_api.py                  # Tests funcionales de la API (121 funciones test_)
│   └── test_security.py             # Tests de seguridad y aislamiento (16 funciones test_)
└── app/
    └── ...                          # Código fuente (no meter tests aquí)
```

### 3.2 Configuración (`backend/pytest.ini`)

```ini
[pytest]
asyncio_mode = auto
```

El modo `auto` permite que las funciones `async def test_...` se ejecuten
sin necesidad del decorador `@pytest.mark.asyncio` explícito en cada test.

### 3.3 El `conftest.py` — fixtures centrales

El fichero `backend/tests/conftest.py` (310 líneas) define las fixtures que
todos los tests del backend usan. Es crítico entenderlo antes de escribir
tests nuevos.

#### Variables de entorno de test

El `conftest.py` fija variables de entorno seguras para tests antes de
importar la aplicación:

```python
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("PIN_HASH_SALT", "test-salt")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("STRIPE_SECRET_KEY", "***")
os.environ.setdefault("TEST_STRIPE_SECRET_KEY", "***")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_webhook_secret_32bytes_long")
```

> **Importante:** si tu test necesita una variable de entorno distinta,
> configúrala dentro del propio test con `monkeypatch.setenv(...)` antes de
> que se importe la aplicación, o ajusta el `conftest.py` con un fixture nuevo.

#### Fixtures disponibles

| Fixture | Scope | Descripción |
|---------|-------|-------------|
| `event_loop` | `session` | Un único event loop para toda la sesión de tests. |
| `setup_database` | `function` (autouse) | Crea tablas antes de cada test, las elimina después. Resetea los stores del rate limiter. |
| `seed_data` | `function` | Inserta dos tenants, owners, un manager, turnos, empleados con PINs conocidos, vacaciones, bajas y festivos. Devuelve un dict con IDs y tokens JWT. |
| `db_session` | `function` | Sesión limpia de SQLAlchemy para consultas directas en tests. |
| `client` | `function` | `AsyncClient` de httpx wired a la app FastAPI vía `ASGITransport`. |

#### Qué proporciona `seed_data`

El fixture `seed_data` devuelve un diccionario con todo lo que un test
necesita para interactuar con la API:

```python
{
    "admin_id": "...",
    "admin_token": "JWT...",          # super_admin, sin tenant
    "owner_a_id": "...",
    "owner_a_token": "JWT...",         # owner del Tenant A
    "owner_b_id": "...",
    "owner_b_token": "JWT...",         # owner del Tenant B (para aislamiento)
    "manager_a_token": "JWT...",       # manager del Tenant A
    "tenant_a_id": "...",
    "tenant_b_id": "...",
    "emp1_id": "...",                  # Carlos López, PIN 1234, NFC NFC001
    "emp2_id": "...",                  # Ana Martínez, PIN 5678, NFC NFC002
    "emp_b1_id": "...",               # Pedro TenantB (para cross-tenant)
    "shift_morning_id": "...",         # Mañana 8:00-16:00
    "shift_afternoon_id": "...",      # Tarde 16:00-00:00
    "vac1_id": "...",                  # Vacaciones pending de emp1
    "leave1_id": "...",                # Baja médica de emp2
    "holiday1_id": "...",              # Navidad 25/12
}
```

Los PINs y credenciales conocidas para usar en tests:

| Usuario | Email | Password | PIN (empleado) | Rol |
|---------|-------|----------|----------------|-----|
| Admin | `admin@talentup.es` | `admin123` | — | super_admin |
| Owner A | `owner@latagliatella.es` | `owner123` | — | owner |
| Owner B | `owner@elpuerto.es` | `owner456` | — | owner |
| Manager A | `manager@latagliatella.es` | `manager123` | — | manager |
| Empleado 1 | — | — | `1234` | employee (Tenant A) |
| Empleado 2 | — | — | `5678` | employee (Tenant A) |
| Empleado B | — | — | `9999` | employee (Tenant B) |

### 3.4 Ejecutar los tests del backend

#### Tests rápidos en SQLite (en memoria)

Es la forma más rápida de validar tu código. No requiere PostgreSQL ni
Docker:

```bash
cd backend
DATABASE_URL="sqlite+aiosqlite://" python -m pytest --tb=short -q
```

O simplemente (el `conftest.py` ya pone SQLite por defecto):

```bash
cd backend
python -m pytest --tb=short -q
```

#### Tests con cobertura

```bash
cd backend
python -m pytest --cov=app --cov-report=term-missing --cov-report=html
# Informe HTML en backend/htmlcov/index.html
```

Para un reporte XML (lo que sube Codecov):

```bash
cd backend
python -m pytest --cov=app --cov-report=xml
# Genera backend/coverage.xml
```

#### Ejecutar un test o fichero concreto

```bash
cd backend

# Un fichero completo
python -m pytest tests/test_security.py -v

# Un test por nombre (coincidencia parcial)
python -m pytest -k "aislamiento" -v

# Un test exacto
python -m pytest tests/test_security.py::test_owner_no_puede_ver_empleados_de_otro_tenant -v

# Mostrar salida de prints
python -m pytest tests/test_api.py -s -v
```

#### Tests en PostgreSQL local

Requiere Docker y `docker-compose.yml` del repo:

```bash
# Desde la raíz del repo
docker compose up -d db

# Espera a que PostgreSQL esté listo
docker compose exec -T db pg_isready -U postgres

# Crea la base de datos de test
docker compose exec -T db psql -U postgres -c "CREATE DATABASE talentup_test;"

# Ejecuta migraciones
cd backend
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  alembic upgrade head

# Ejecuta tests
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  PIN_HASH_SALT="test-salt" JWT_SECRET="test-secret" \
  python -m pytest tests/ --tb=short -q

# Limpieza
cd ..
docker compose down
```

### 3.5 Cómo se inicializa la base de datos en tests

El fixture `setup_database` (autouse, scope `function`) hace lo siguiente antes
de cada test:

1. Limpia los stores en memoria del rate limiter (`_pin_limits`, `_nfc_limits`,
   `_qr_limits`, `_login_limits`, `_tenant_clock_limits`).
2. Ejecuta `await init_db()` que crea todas las tablas con
   `Base.metadata.create_all` en la base de datos de test (SQLite en memoria
   por defecto).
3. Tras el test, hace `Base.metadata.drop_all` y `engine.dispose()` para
   liberar conexiones.

> **Nota:** los tests **no usan Alembic** para crear el esquema; usan
   `Base.metadata.create_all` directamente. Alembic solo se ejecuta en el
   job de PostgreSQL del CI para validar que las migraciones son correctas.

---

## 4. Backend — Migración de SQLite a PostgreSQL

### 4.1 Estado actual

Actualmente los **64 tests del backend corren solo en SQLite** en el
desarrollo local y en el job `test` del workflow `ci.yml`. El workflow
`backend-ci.yml` añade un job `test-postgres` que ejecuta los mismos tests
contra PostgreSQL 16 mediante `docker-compose`.

### 4.2 Por qué importa la migración

SQLite y PostgreSQL tienen diferencias que pueden ocultar bugs en producción:

- **Tipos**: SQLite es débilmente tipado; PostgreSQL es estricto. Un `String`
  en SQLite admite cualquier valor; en PostgreSQL falla si no coincide el tipo.
- **Concurrencia**: SQLite serializa escrituras; PostgreSQL permite
  concurrencia real con `SELECT ... FOR UPDATE` y niveles de aislamiento.
- **Funciones**: `strftime`, `datetime()`, manejo de booleanos y
  case-sensitivity en `LIKE` difieren.
- **Row-Level Security**: el `rls.py` del backend asume capacidades de
  PostgreSQL que SQLite no tiene de forma nativa.

### 4.3 Qué verificar al migrar

Si tu test o tu código usa alguno de los siguientes, **debes** ejecutarlo
también contra PostgreSQL (local o CI) antes de mergear:

1. **Consultas con `LIKE` o `ILIKE`**: SQLite es case-insensitive por defecto
   en `LIKE` con ASCII; PostgreSQL distingue mayúsculas. Usa `ILIKE` si
   necesitas insensibilidad.
2. **Booleans**: SQLite los almacena como 0/1; PostgreSQL como `true/false`.
   Verifica que los modelos declaran `Boolean` y no `Integer`.
3. **Timestamps**: SQLite no tiene timezone; PostgreSQL sí. Usa
   `TIMESTAMP(timezone=True)` o `DateTime(timezone=True)` en los modelos.
4. **JSON/JSONB**: si usas columnas JSON, el comportamiento de consultas
   difiere. PostgreSQL tiene `->` y `->>` nativos; SQLAlchemy abstrae pero
   conviene probar.
5. **Constraints**: `UNIQUE`, `CHECK`, `FOREIGN KEY` se aplican en SQLite
   solo si `PRAGMA foreign_keys = ON`. PostgreSQL siempre los aplica.
6. **Migraciones Alembic**: genera la migración con `--autogenerate` contra
   PostgreSQL, no contra SQLite, para que los tipos sean correctos.

### 4.4 Cómo correr ambos en local

El flujo recomendado durante el desarrollo:

```bash
# 1. Desarrollo iterativo rápido — SQLite en memoria
cd backend
python -m pytest -q

# 2. Antes de abrir el PR — PostgreSQL via docker-compose
cd ..
docker compose up -d db
docker compose exec -T db psql -U postgres -c "CREATE DATABASE talentup_test;"
cd backend
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  alembic upgrade head
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  python -m pytest tests/ -q
cd ..
docker compose down
```

### 4.5 Pendientes de cobertura de tests

Según `ROADMAP.md`, las áreas sin cobertura suficiente son:

- **Billing / Stripe**: webhooks, suscripciones, facturación.
- **Payroll**: cálculo de nóminas, horas extra, exportaciones.
- **Migración completa a PostgreSQL** en local (no solo CI).

Añadir tests en estas áreas es prioridad alta para el roadmap.

---

## 5. Frontend — vitest (unitarios)

El frontend usa **vitest** con entorno **jsdom** para tests unitarios de la
lógica de la SPA. No requiere un navegador real ni un servidor levantado.

### 5.1 Estructura

```
frontend/
├── package.json              # type: module, scripts.test = "vitest run"
├── vitest.config.js          # Configuración de vitest
├── src/
│   └── app.js                 # Lógica principal (lo que se testea)
└── tests/
    ├── setup.js               # Setup de jsdom, mocks de fetch
    └── app.test.js            # Suite de tests (373 líneas)
```

### 5.2 Configuración (`frontend/vitest.config.js`)

```javascript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.js'],
    setupFiles: ['tests/setup.js'],
  },
});
```

- **`environment: 'jsdom'`**: simula el DOM en Node para que `document`,
  `window`, `localStorage` y `fetch` estén disponibles.
- **`include: ['tests/**/*.test.js']`**: cualquier fichero `.test.js` dentro
  de `tests/` se ejecuta como test.
- **`setupFiles: ['tests/setup.js']`**: se carga antes de cada suite para
  inicializar el entorno (mocks de `fetch`, `localStorage`, etc.).

### 5.3 El `tests/setup.js`

Proporciona helpers que los tests usan para controlar el comportamiento de
`fetch` sin hacer llamadas reales:

- `clearFetchCalls()`: resetea el registro de llamadas a `fetch`.
- `setFetchResponse(data)`: hace que el siguiente `fetch` devuelva `data`
  como JSON.
- Mocks de `localStorage`, `window.location` y otras APIs del navegador.

### 5.4 Qué cubre `app.test.js`

La suite importa funciones de `../src/app.js` y testea:

| Función / bloque | Cobertura |
|------------------|-----------|
| `state` | Estado global de la SPA |
| `api` | Wrapper de llamadas a la API |
| `navigate` | Navegación entre vistas del dashboard |
| `filterEmpleados` | Filtrado de lista de empleados |
| `renderEmpleadosPage` | Render de la vista de empleados |
| `loadEmpleados`, `loadTurnos`, `loadDashboard` | Carga de datos desde la API |
| `showToast`, `openModal`, `closeModal`, `saveModal` | UI: notificaciones y modales |
| `enterApp`, `logout` | Flujo de autenticación |
| `getInitialToken`, `isTokenExpired`, `decodeJwt` | Gestión de JWT |
| `updateOnlineStatus`, `updateDemoBanner` | Estado de conexión y banner demo |
| `filterFichajes`, `filterVacaciones`, `filterBajas` | Filtrado de listas |

El `beforeEach` resetea el estado compartido para evitar fugas entre tests:

```javascript
beforeEach(() => {
  clearFetchCalls();
  setFetchResponse(null);
  Object.assign(state, {
    user: null,
    employees: [],
    shifts: [],
    schedules: [],
    clockHistory: [],
    overtime: [],
    vacations: [],
    leaves: [],
    holidays: [],
    // ...
  });
});
```

### 5.5 Ejecutar los tests del frontend

```bash
cd frontend

# Instala dependencias (solo la primera vez)
npm install

# Ejecuta todos los tests unitarios (equivale a: npx vitest run)
npm test

# Modo watch durante desarrollo (re-ejecuta al guardar)
npx vitest

# Con cobertura
npx vitest run --coverage

# Un fichero concreto
npx vitest run tests/app.test.js

# Modo UI interactivo
npx vitest --ui
```

### 5.6 Dependencias de test

`frontend/package.json` declara:

```json
{
  "type": "module",
  "scripts": { "test": "vitest run" },
  "devDependencies": {
    "@playwright/test": "^1.61.1",
    "jsdom": "^24.1.0",
    "vitest": "^1.6.0"
  },
  "dependencies": {
    "playwright": "^1.61.1"
  }
}
```

> **Regla:** el frontend de producción no debe añadir dependencias en
   `dependencies`. Solo se permiten `devDependencies` para tests.

---

## 6. Frontend — Playwright (e2e)

Los tests end-to-end usan **Playwright** contra un navegador Chromium
headless. A diferencia de vitest, **sí requieren** que el backend y el
frontend estén corriendo en local.

### 6.1 Estructura

```
frontend/
├── playwright.config.js       # Configuración de Playwright
├── e2e/
│   └── talentup.spec.cjs      # Spec de tests e2e
└── package.json
```

> **Nota:** el spec está en `e2e/`, **no** en `tests/`. La configuración de
   vitest incluye `tests/**/*.test.js` y la de Playwright usa `testDir:
   './tests/e2e'` según `playwright.config.js` (ubicación configurable).

### 6.2 Configuración (`frontend/playwright.config.js`)

```javascript
module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [],   // No lanza servidores automáticamente
});
```

Puntos clave:

- **`baseURL: 'http://localhost:3000'`**: el frontend debe servirse en el
  puerto 3000.
- **`webServer: []`**: Playwright **no levanta** los servidores. Tú debes
  tener corriendo:
  - Backend en `http://localhost:8000`
  - Frontend/landing en `http://localhost:3000`
- **`retries: process.env.CI ? 2 : 0`**: en CI reintenta 2 veces; en local no.
- **`headless: true`**: sin ventana de navegador visible por defecto.

### 6.3 Credenciales de test

El spec usa variables de entorno con valores por defecto que coinciden con
el `seed_data` del backend:

```javascript
const LOGIN_EMAIL = process.env.TEST_LOGIN_EMAIL || 'owner@latagliatella.es';
const LOGIN_PASSWORD = process.env.TEST_LOGIN_PASSWORD || 'owner123';
```

Para usar credenciales distintas:

```bash
TEST_LOGIN_EMAIL="otro@ejemplo.es" TEST_LOGIN_PASSWORD="pass" npx playwright test
```

### 6.4 Qué cubre `talentup.spec.cjs`

- **Landing**: la página de aterrizaje muestra el título y el CTA principal.
- **Login**: un owner puede hacer login y es redirigido al dashboard.
- **Dashboard**: tras login, el navbar muestra el nombre del usuario y las
  secciones de navegación están visibles.
- **Navegación**: se puede cambiar entre vistas del dashboard.
- **Tests móviles**: se ejecutan en el mismo proyecto chromium con viewport
  reducido dentro del test.

### 6.5 Ejecutar los tests e2e

#### Prerrequisitos

1. **Backend corriendo** con datos semilla:

```bash
cd backend
python -c "from app.seed import run_seed; run_seed()"  # si existe script de seed
# o ejecuta la app que siembra datos al arrancar
uvicorn app.main:app --reload --port 8000
```

2. **Frontend corriendo** en el puerto 3000:

```bash
cd frontend
npx serve . -l 3000
# o
python -m http.server 3000
```

#### Comandos

```bash
cd frontend

# Instala Playwright y el navegador (solo la primera vez)
npm install
npx playwright install chromium

# Ejecuta todos los tests e2e
npx playwright test

# Modo interactivo (UI con inspector)
npx playwright test --ui

# Un fichero concreto
npx playwright test e2e/talentup.spec.cjs

# Ver el reporte HTML de resultados
npx playwright show-report

# Modo debug (paso a paso con inspector)
npx playwright test --debug

# Un test por nombre
npx playwright test -g "Login con owner"
```

#### Sin ventana (headless, por defecto)

Los tests corren headless. Si quieres ver el navegador:

```bash
npx playwright test --headed
```

---

## 7. Firmware — PlatformIO y pytest

El firmware del ESP32 CYD se testea de dos formas:

1. **Tests unitarios en Python** (`test/test_firmware.py`): portan la lógica
   del `.ino` a Python con mocks de todo el hardware (WiFi, TFT, PN532,
   SPIFFS, HTTPClient, OTA, watchdog). **No requiere Arduino ni hardware
   real.** Se ejecutan con pytest.
2. **Compilación con PlatformIO** (`pio run`): valida que el firmware compila
   para el target `esp32dev`. No ejecuta tests en CI, solo build.

### 7.1 Estructura

```
hardware/esp32_fichaje_cyd/
├── platformio.ini            # Config PlatformIO (board esp32dev, lib_deps)
├── src/
│   └── esp32_fichaje_cyd.ino  # Firmware principal (Arduino)
└── test/
    └── test_firmware.py       # Tests unitarios Python con mocks
```

### 7.2 Tests unitarios Python (`test_firmware.py`)

El fichero `test/test_firmware.py` porta las constantes y la lógica del
firmware a Python y la testea contra mocks:

- **WiFi**: conexión, reconexión, timeouts.
- **PN532 (NFC)**: lectura de UID, debounce de 3 segundos.
- **TFT_eSPI**: render de pantalla, reloj, estados.
- **SPIFFS**: persistencia de configuración.
- **HTTPClient**: envío de fichajes al backend.
- **ArduinoOTA**: actualizaciones over-the-air.
- **Watchdog (WDT)**: gestión de tareas.

No hay toolchain de Arduino ni un dispositivo físico: todo es simulado con
`unittest.mock.MagicMock` y `patch`.

#### Ejecutar

```bash
cd hardware/esp32_fichaje_cyd
python -m pytest test/ -q

# Con verbosidad
python -m pytest test/ -v

# Un test concreto
python -m pytest test/test_firmware.py -k "nfc" -v
```

### 7.3 Compilación con PlatformIO

Para validar que el firmware compila (requisito del CI):

```bash
cd hardware/esp32_fichaje_cyd
pio run

# Compilar y flashear (requiere dispositivo conectado)
pio run -t upload --upload-port /dev/ttyUSB0   # Linux/macOS
pio run -t upload --upload-port COM4            # Windows

# Monitor serie
pio device monitor
```

### 7.4 Configuración de hardware

Antes de flashear, edita `platformio.ini` con tus credenciales:

```ini
build_flags =
    -DWIFI_SSID=\"TU_WIFI\"
    -DWIFI_PASS=\"TU_PASSWORD\"
    -DBACKEND_URL=\"http://192.168.1.100:8000\"
    -DTENANT_ID=\"default\"
```

> **Advertencia:** no commitees tus credenciales reales en `platformio.ini`.
   Usa variables de entorno o un fichero local no versionado.

### 7.5 Tests de hardware manual

Los tests de integración con hardware real son manuales y no están
automatizados en CI. El checklist para validar un dispositivo físico:

1. Flashear el firmware (`pio run -t upload`).
2. Verificar que conecta al WiFi (monitor serie muestra IP).
3. Aproximar una tarjeta NFC y verificar que lee el UID.
4. Verificar que envía el fichaje al backend (log del backend).
5. Comprobar la pantalla TFT muestra el estado y la hora.
6. Probar OTA: subir una nueva versión por WiFi y verificar que se aplica.

---

## 8. CI/CD — GitHub Actions

El repositorio tiene **cuatro workflows** en `.github/workflows/`:

### 8.1 `ci.yml` — CI principal

Se ejecuta en push a `main` y `develop`, y en PR a `main`.

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
```

Jobs:

1. **`test`** (Ubuntu, Python 3.11):
   - Instala dependencias del backend.
   - Ejecuta `pytest --tb=short -q` con `DATABASE_URL=sqlite+aiosqlite://`.
   - Calcula cobertura con `pytest-cov` y genera `coverage.xml`.
   - Sube el reporte a **Codecov** (`codecov/codecov-action@v4`).
2. **`firmware`** (Ubuntu, Python 3.11, `continue-on-error: true`):
   - Instala PlatformIO.
   - Compila el firmware con `pio run` en `hardware/esp32_fichaje_cyd`.
   - Si falla por librerías faltantes en CI, no rompe el pipeline.

### 8.2 `backend-ci.yml` — CI avanzado del backend

Se ejecuta en push y PR a `master` cuando cambian ficheros de `backend/`,
el propio workflow o `docker-compose.yml`.

Jobs:

1. **`test-sqlite`**: igual que el `test` de `ci.yml`, SQLite en memoria.
2. **`test-postgres`**: levanta PostgreSQL 16 con `docker-compose`, crea la
   base de datos `talentup_test`, ejecuta `alembic upgrade head` y luego
   `pytest tests/ --tb=short -q`. Al final siempre hace `docker compose down`.
3. **`build-and-push`** (solo en push a `master`): construye la imagen Docker
   del backend y la sube a **GitHub Container Registry** (`ghcr.io`) con
   tags `sha`, `latest` y `master`.

### 8.3 `deploy-backend.yml` — Deploy a Railway

Se ejecuta en push a `main`/`master` cuando cambian `backend/**` o el
`Dockerfile`. Usa la CLI de Railway (`@railway/cli`) para desplegar la
imagen.

### 8.4 `deploy-frontend.yml` — Deploy a GitHub Pages

Se ejecuta en push a `master` cuando cambian `frontend/**`. Publica el
frontend en GitHub Pages con `actions/configure-pages` y
`actions/deploy-pages`.

### 8.5 Orden de checks obligatorios

Para que un PR se pueda mergear a `main`:

1. `test` (ci.yml) debe pasar — SQLite.
2. `test-sqlite` y `test-postgres` (backend-ci.yml) deben pasar si el PR
   toca `backend/`.
3. `firmware` (ci.yml) puede fallar sin bloquear (`continue-on-error: true`).
4. Codecov se sube pero no bloquea el merge (`fail_ci_if_error: false`).

### 8.6 Cómo reproducir el CI localmente

```bash
# Job test de ci.yml (SQLite)
cd backend
pip install -r requirements.txt pytest pytest-asyncio httpx
DATABASE_URL="sqlite+aiosqlite://" python -m pytest --tb=short -q

# Job test-postgres de backend-ci.yml
cd ..  # raíz del repo
docker compose up -d db
docker compose exec -T db psql -U postgres -c "CREATE DATABASE talentup_test;"
cd backend
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  alembic upgrade head
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  python -m pytest tests/ --tb=short -q
cd ..
docker compose down

# Job firmware de ci.yml
cd hardware/esp32_fichaje_cyd
pip install platformio
pio run
```

---

## 9. Cómo ejecutar todo localmente

### 9.1 Flujo completo antes de abrir un PR

```bash
# 0. Sincroniza tu fork
git checkout main
git fetch upstream
git merge upstream/main

# 1. Backend — SQLite (rápido)
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt pytest pytest-asyncio pytest-cov httpx
DATABASE_URL="sqlite+aiosqlite://" python -m pytest --tb=short -q

# 2. Backend — PostgreSQL (valida migración)
cd ..
docker compose up -d db
docker compose exec -T db psql -U postgres -c "CREATE DATABASE talentup_test;"
cd backend
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  alembic upgrade head
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  python -m pytest tests/ --tb=short -q
cd ..
docker compose down

# 3. Frontend — vitest (unit)
cd frontend
npm install
npm test

# 4. Frontend — Playwright (e2e, requiere backend + frontend corriendo)
# Terminal 1: backend
cd ../backend && uvicorn app.main:app --reload --port 8000 &
# Terminal 2: frontend
cd ../frontend && npx serve . -l 3000 &
npx playwright install chromium
npx playwright test

# 5. Firmware — tests Python (opcional si no tocas hardware)
cd ../hardware/esp32_fichaje_cyd
python -m pytest test/ -q
```

### 9.2 Script de verificación rápida

Puedes ejecutar solo backend (SQLite) + frontend (vitest) para un feedback
muy rápido en menos de un minuto:

```bash
# Backend SQLite
cd backend && python -m pytest -q && cd ..

# Frontend vitest
cd frontend && npm test && cd ..
```

---

## 10. Cómo añadir nuevos tests

### 10.1 Añadir un test de backend (pytest)

1. **Decide el fichero**: tests de API van en `test_api.py`; tests de
   seguridad y aislamiento van en `test_security.py`. Si creas un área
   nueva (p. ej. billing), puedes crear `test_billing.py`.

2. **Usa las fixtures existentes**: importa `seed_data` y `client` como
   argumentos del test. No crees tu propia base de datos.

```python
# backend/tests/test_api.py

async def test_crear_empleado_asigna_tenant_correcto(client, seed_data):
    """Un owner solo puede crear empleados en su propio tenant."""
    headers = {"Authorization": f"Bearer {seed_data['owner_a_token']}"}
    payload = {
        "name": "Nuevo Empleado",
        "dni": "11111111X",
        "pin": "4321",
        "shift_id": seed_data["shift_morning_id"],
    }
    resp = await client.post("/employees", json=payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["tenant_id"] == seed_data["tenant_a_id"]
```

3. **Testea el aislamiento multi-tenant** cuando corresponda:

```python
# backend/tests/test_security.py

async def test_owner_a_no_ve_empleados_de_tenant_b(client, seed_data):
    """Owner A no puede listar empleados de Tenant B."""
    headers = {"Authorization": f"Bearer {seed_data['owner_a_token']}"}
    resp = await client.get("/employees", headers=headers)
    assert resp.status_code == 200
    empleados = resp.json()
    # Ningún empleado debe pertenecer a Tenant B
    for emp in empleados:
        assert emp["tenant_id"] != seed_data["tenant_b_id"]
```

4. **Nombres en español descriptivos**: `test_<qué_se_verifica>`. Usa
   snake_case. El nombre debe describir la intención, no la implementación.

5. **Ejecuta el test**:

```bash
cd backend
python -m pytest tests/test_api.py::test_crear_empleado_asigna_tenant_correcto -v
```

6. **Verifica en PostgreSQL** si tu test toca tipos o queries sensibles al
   dialecto (ver [§4](#4-backend--migración-de-sqlite-a-postgresql)).

### 10.2 Añadir un test de frontend (vitest)

1. **Añade un bloque `describe` o `it`** en `frontend/tests/app.test.js`
   (o crea un nuevo `*.test.js` en `tests/`).

2. **Importa lo que necesites** de `src/app.js`:

```javascript
import { describe, it, expect, beforeEach } from 'vitest';
import { filterEmpleados, state } from '../src/app.js';

describe('filterEmpleados', () => {
  beforeEach(() => {
    state.employees = [
      { id: 1, name: 'Carlos', is_active: true },
      { id: 2, name: 'Ana', is_active: false },
    ];
  });

  it('filtra solo empleados activos', () => {
    const resultado = filterEmpleados({ solo_activos: true });
    expect(resultado).toHaveLength(1);
    expect(resultado[0].name).toBe('Carlos');
  });
});
```

3. **Usa los helpers de `setup.js`** para controlar `fetch`:

```javascript
import { clearFetchCalls, setFetchResponse } from './setup.js';

beforeEach(() => {
  clearFetchCalls();
  setFetchResponse({ data: [] });
});
```

4. **Ejecuta**:

```bash
cd frontend
npx vitest run tests/app.test.js
```

### 10.3 Añadir un test e2e (Playwright)

1. **Añade un `test`** en `frontend/e2e/talentup.spec.cjs` (o crea un nuevo
   `.spec.cjs` en `e2e/`).

```javascript
test('Crear empleado desde el dashboard', async ({ page }) => {
  // Login
  await page.goto('/');
  await page.fill('#login-email', 'owner@latagliatella.es');
  await page.fill('#login-password', 'owner123');
  await page.click('#login-btn');

  // Navegar a empleados
  await page.click('[data-nav="empleados"]');
  await page.click('#btn-nuevo-empleado');

  // Rellenar y guardar
  await page.fill('#emp-name', 'Test E2E');
  await page.fill('#emp-dni', '99999999X');
  await page.fill('#emp-pin', '0000');
  await page.click('#btn-guardar-empleado');

  // Verificar que aparece en la lista
  await expect(page.locator('text=Test E2E')).toBeVisible();
});
```

2. **Requisitos**: backend y frontend corriendo en `:8000` y `:3000`.

3. **Ejecuta**:

```bash
cd frontend
npx playwright test e2e/talentup.spec.cjs -g "Crear empleado"
```

### 10.4 Añadir un test de firmware (Python)

1. **Porta la lógica** que quieres testear a Python en
   `hardware/esp32_fichaje_cyd/test/test_firmware.py`.

2. **Usa mocks** para el hardware:

```python
def test_debounce_nfc_evita_fichaje_doble():
    """Un mismo UID no debe generar dos fichajes en menos de 3 segundos."""
    nfc_mock = MagicMock()
    nfc_mock.read_uid.return_value = "ABC123"

    estado = EstadoFirmware()
    estado.procesar_nfc(nfc_mock.read_uid())
    fichajes_antes = len(estado.fichajes)

    # Segunda lectura inmediata (dentro del debounce de 3000ms)
    estado.procesar_nfc(nfc_mock.read_uid())

    assert len(estado.fichajes) == fichajes_antes  # no se añade nuevo
```

3. **Ejecuta**:

```bash
cd hardware/esp32_fichaje_cyd
python -m pytest test/test_firmware.py -k "debounce" -v
```

---

## 11. Cobertura y métricas

### 11.1 Cobertura del backend

El CI calcula cobertura con `pytest-cov`:

```bash
cd backend
python -m pytest --cov=app --cov-report=term-missing
```

El reporte `term-missing` muestra, por módulo, las líneas no cubiertas:

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
app/routers/billing.py              45     30    33%   12-40, 50-62
app/routers/clock.py                60      5    92%   34, 78
...
```

El reporte XML (`coverage.xml`) se sube a Codecov en cada ejecución de CI.
Puedes ver el histórico en la integración de Codecov del repositorio.

### 11.2 Objetivos de cobertura

No hay una puerta estricta, pero las directrices son:

- **`app/routers/`**: objetivo 80%. Áreas críticas (auth, clock, rls) aspiran
  a 90%+.
- **`app/security` y `app/rls`**: objetivo 90%. Nunca debe bajar.
- **`app/routers/billing.py` y `app/routers/payroll.py`**: actualmente baja,
  prioridad del roadmap subirla.
- **Frontend**: vitest no genera cobertura por defecto; se puede activar con
  `--coverage` cuando se quiera medir.

### 11.3 Cuándo exigir tests en un PR

- **Cualquier PR que añade un endpoint** → debe incluir al menos un test
  funcional que lo llame vía `client`.
- **Cualquier PR que añade un modelo** → debe incluir un test de creación
  y, si tiene relaciones, de las relaciones.
- **Cualquier PR que cambia lógica de multi-tenancy** → debe incluir tests
  de aislamiento que verifiquen que un tenant no ve datos de otro.
- **Cualquier PR que cambia la lógica del frontend en `app.js`** → debe
  añadir o actualizar tests en `app.test.js`.

---

## 12. Solución de problemas

### 12.1 Backend

#### `ModuleNotFoundError: No module named 'app'`

Estás ejecutando pytest desde el directorio equivocado. Entra en `backend/`:

```bash
cd backend
python -m pytest -q
```

#### `RuntimeError: Event loop is closed`

pytest-asyncio está mal configurado. Verifica que `backend/pytest.ini`
contiene `asyncio_mode = auto` y que no hay un `conftest.py` que lo
sobrescriba.

#### Tests fallan en PostgreSQL pero pasan en SQLite

- **Case-sensitivity en `LIKE`**: usa `ILIKE` o `func.lower()`.
- **Booleanos como enteros**: el modelo debe declarar `Column(Boolean)`.
- **Timezones**: usa `DateTime(timezone=True)` en el modelo.
- **Constraints FK**: PostgreSQL los aplica siempre; SQLite no. Verifica
  que los datos semilla cumplen las FK.

#### `alembic upgrade head` falla en PostgreSQL

- Verifica que la base de datos `talentup_test` existe.
- Ejecuta `alembic history` para ver el orden de migraciones.
- Si una migración es específica de SQLite, añade una guarda
  `if op.get_bind().dialect.name == 'sqlite':`.

### 12.2 Frontend (vitest)

#### `Cannot find module '../src/app.js'`

Estás ejecutando vitest desde el directorio equivocado. Entra en `frontend/`:

```bash
cd frontend
npx vitest run
```

#### `ReferenceError: document is not defined`

El entorno no es jsdom. Verifica `vitest.config.js` tiene
`environment: 'jsdom'` y que `jsdom` está instalado (`npm install`).

#### `fetch is not defined`

El `setup.js` debe mockear `global.fetch`. Verifica que se carga en
`setupFiles` y que `clearFetchCalls`/`setFetchResponse` están exportados.

### 12.3 Frontend (Playwright)

#### `Error: webServer ... failed to start`

Playwright no levanta servidores (`webServer: []`). Debes tener el backend
en `:8000` y el frontend en `:3000` corriendo manualmente.

#### Tests se saltan o no se encuentran

Verifica que el spec está en el directorio configurado por `testDir` en
`playwright.config.js` (actualmente `./tests/e2e`). Si tu spec está en
`e2e/`, ajusta `testDir` o muévelo.

#### `browserType.launch: Executable doesn't exist`

Falta instalar el navegador:

```bash
cd frontend
npx playwright install chromium
```

### 12.4 Firmware

#### `ModuleNotFoundError: No module named 'pytest'`

Instala pytest en tu entorno Python:

```bash
pip install pytest
```

#### `pio run` falla con errores de librerías

PlatformIO no ha descargado las dependencias. Ejecuta:

```bash
cd hardware/esp32_fichaje_cyd
pio pkg install
```

En CI el job de firmware tiene `continue-on-error: true` precisamente porque
las librerías de PlatformIO a veces fallan en el runner.

---

## 13. Apéndice: referencia de fixtures

### 13.1 Fixtures del backend (`conftest.py`)

| Fixture | Scope | Autouse | Devuelve | Uso típico |
|---------|-------|---------|----------|------------|
| `event_loop` | session | no | event loop | Interno de pytest-asyncio |
| `setup_database` | function | **sí** | None (yield) | Inicializa/drop DB por test |
| `seed_data` | function | no | dict con IDs y tokens | Inyectar datos en tests |
| `db_session` | function | no | AsyncSession | Consultas directas a DB |
| `client` | function | no | AsyncClient | Llamadas HTTP a la API |

### 13.2 Helpers del frontend (`tests/setup.js`)

| Helper | Descripción |
|--------|-------------|
| `clearFetchCalls()` | Resetea el registro de llamadas a `fetch` |
| `setFetchResponse(data)` | Configura la próxima respuesta de `fetch` |

### 13.3 Variables de entorno de test

| Variable | Valor de test | Dónde se fija |
|----------|---------------|---------------|
| `DATABASE_URL` | `sqlite+aiosqlite://` | `conftest.py` (override en CLI para PG) |
| `PIN_HASH_SALT` | `test-salt` | `conftest.py` |
| `JWT_SECRET` | `test-secret` | `conftest.py` |
| `STRIPE_SECRET_KEY` | `***` | `conftest.py` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_test_...` | `conftest.py` |
| `APP_ENV` | `test` | CI (`backend-ci.yml`) |
| `TEST_LOGIN_EMAIL` | `owner@latagliatella.es` | Playwright spec (con fallback) |
| `TEST_LOGIN_PASSWORD` | `owner123` | Playwright spec (con fallback) |

---

*Documento mantenido por el equipo de TalentUP Fichaje. Última actualización:
agosto 2026. Si encuentras un error, un test que falta documentar o una
sección desactualizada, abre un PR con el cambio — esta guía también se
testea con contribuciones.*