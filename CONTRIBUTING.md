# Guía de Contribución — TalentUP Fichaje

> **Repo:** [github.com/jordialbarracin/talentup-fichaje](https://github.com/jordialbarracin/talentup-fichaje)
> **Licencia:** Propietaria (ver `LICENSE` si existe)
> **Documentación relacionada:** `ROADMAP.md`, `TESTING.md`, `ARCHITECTURE_AUDIT.md`, `DEPLOY.md`

Bienvenido/a al equipo de contribución de **TalentUP Fichaje**, el SaaS de fichaje
digital para hostelería que cumple el **RD-ley 8/2019**. Esta guía describe cómo
configurar tu entorno, cómo está organizado el repositorio, qué convenciones
seguimos al escribir commits y pull requests, y cómo ejecutar las suites de tests
antes de enviar tu código.

---

## Tabla de contenidos

1. [Código de conducta](#1-código-de-conducta)
2. [Requisitos del entorno](#2-requisitos-del-entorno)
3. [Configuración inicial](#3-configuración-inicial)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Convenciones de commits](#5-convenciones-de-commits)
6. [Flujo de trabajo con Git](#6-flujo-de-trabajo-con-git)
7. [Proceso de Pull Request](#7-proceso-de-pull-request)
8. [Testing](#8-testing)
9. [Estilo de código](#9-estilo-de-código)
10. [Despliegue y entornos](#10-despliegue-y-entornos)
11. [Roadmap y prioridades](#11-roadmap-y-prioridades)
12. [Contacto y soporte](#12-contacto-y-soporte)

---

## 1. Código de conducta

Al participar en este proyecto aceptas cumplir el siguiente código de conducta.
Esperamos comportamiento colaborativo, respetuoso y profesional en todos los
canales oficiales (issues, PRs, revisiones, commits y discusiones).

### Nuestros compromisos

- **Respeto** hacia todas las personas contribuidoras, independientemente de su
  nivel de experiencia, identidad de género, orientación sexual, discapacidad,
  apariencia física, etnia, religión o nacionalidad.
- **Constructividad**: las críticas se dirigen al código, nunca a la persona.
  Usa lenguaje técnico y neutral. Si una revisión genera tensión, páusala y
  resuélvela de forma asistida por un maintainer.
- **Transparencia**: todas las decisiones relevantes se documentan en issues,
  PRs o `ROADMAP.md`. No hay acuerdos privados que afecten al código público.

### Comportamientos inaceptables

- Insultos, comentarios despectivos o ataques personales.
- *Doxxing* o exposición de datos privados de otros contribuidores.
- Acoso de cualquier tipo (sexual, profesional, social).
- Uso de lenguaje excluyente o discriminatorio en código, documentación o
  comunicación escrita.

### Cumplimiento

Las violaciones se reportan de forma confidencial a los maintainers. Las
sanciones pueden ir desde una advertencia privada hasta el bloqueo permanente
del acceso al repositorio. Este código de conducta se inspira en el
[Contributor Covenant 2.1](https://www.contributor-covenant.org/es/version/2/1/code_of_conduct/)
adaptado al contexto del proyecto.

---

## 2. Requisitos del entorno

Antes de clonar y ejecutar el proyecto necesitas tener instalado lo siguiente.
Las versiones mínimas son **obligatorias** para que los tests y el CI pasen de
forma consistente.

### 2.1 Herramientas base

| Herramienta | Versión mínima | Para qué se usa |
|-------------|----------------|-----------------|
| **git** | 2.40+ | Control de versiones |
| **Python** | 3.11+ | Backend FastAPI y tests de firmware |
| **Node.js** | 18 LTS+ | Frontend (vitest, playwright) y Railway CLI |
| **pip** | 23+ | Gestión de dependencias Python |
| **PlatformIO Core** | 6.1+ | Compilación y tests del firmware ESP32 |
| **Docker** (opcional) | 24+ | PostgreSQL local y build de imágenes |
| **docker-compose** | 2.20+ | Levantar PostgreSQL y Redis para tests locales |

### 2.2 Verificación rápida

```bash
git --version           # >= 2.40
python --version        # >= 3.11
node --version          # >= 18
pip --version           # >= 23
pio --version           # PlatformIO Core >= 6.1 (opcional si no tocas firmware)
docker --version        # opcional
```

### 2.3 Recomendaciones por sistema operativo

- **Windows**: usa Git Bash o MSYS2 para los comandos POSIX de esta guía.
  PowerShell no se ha probado de forma oficial; si lo usas, adapta la sintaxis.
- **macOS**: instala Python 3.11 con `pyenv` o Homebrew (`brew install python@3.11`),
  no uses el Python del sistema.
- **Linux**: usa el gestor de paquetes de tu distro o `pyenv` para aislar
  versiones. PlatformIO se instala mejor vía `pipx`.

---

## 3. Configuración inicial

### 3.1 Fork y clon

```bash
# 1. Haz fork desde GitHub (botón Fork en github.com/jordialbarracin/talentup-fichaje)
# 2. Clona tu fork localmente
git clone https://github.com/<tu-usuario>/talentup-fichaje.git
cd talentup-fichaje

# 3. Añade el upstream para mantener sincronizado tu fork
git remote add upstream https://github.com/jordialbarracin/talentup-fichaje.git
git fetch upstream
```

### 3.2 Backend (FastAPI)

El backend vive en `backend/` y usa Python 3.11 con SQLAlchemy async, FastAPI
y soporte dual SQLite/PostgreSQL.

```bash
cd backend

# Crea y activa un entorno virtual
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows (Git Bash):
source .venv/Scripts/activate

# Instala dependencias
pip install --upgrade pip
pip install -r requirements.txt
# Dependencias de test (no están en requirements.txt):
pip install pytest pytest-asyncio pytest-cov httpx

# Copia las variables de entorno de ejemplo
cp ../.env.example ../.env
# Edita .env con tus valores (DATABASE_URL, JWT_SECRET, PIN_HASH_SALT, etc.)

# Inicializa la base de datos SQLite local
python -m alembic upgrade head
# o, si prefieres crear tablas directamente:
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"

# Arranca el servidor de desarrollo
uvicorn app.main:app --reload --port 8000
```

La documentación interactiva (Swagger) queda disponible en
`http://localhost:8000/docs` y ReDoc en `http://localhost:8000/redoc`.

### 3.3 Frontend (SPA vanilla JS)

El frontend es una SPA en vanilla JavaScript (sin framework) servida como
ficheros estáticos. No necesita build para desarrollo: sirve la carpeta con
cualquier servidor estático.

```bash
cd frontend

# Instala dependencias de test (vitest, playwright, jsdom)
npm install

# Servidor estático de desarrollo (elige uno)
npx serve . -l 3000
# o
python -m http.server 3000
```

Mientras desarrolla, mantén el backend corriendo en `http://localhost:8000`
para que la SPA pueda consumir la API.

### 3.4 Firmware ESP32 CYD

El firmware del dispositivo de fichaje (ESP32-WROOM-32 + TFT ILI9341 + PN532 NFC)
se compila con PlatformIO. **No es obligatorio para contribuir al backend o
frontend**, pero sí si vas a tocar `hardware/`.

```bash
pip install platformio   # o: pipx install platformio

cd hardware/esp32_fichaje_cyd

# Configura tu WiFi y backend en platformio.ini (build_flags)
# Compila
pio run

# Flashea (ajusta el puerto COM/USB)
pio run -t upload --upload-port /dev/ttyUSB0   # Linux/macOS
pio run -t upload --upload-port COM4            # Windows

# Monitor serie
pio device monitor
```

---

## 4. Estructura del repositorio

```
talentup-fichaje/
├── backend/                      # API FastAPI (Python 3.11+)
│   ├── app/
│   │   ├── main.py               # Punto de entrada de FastAPI
│   │   ├── database.py           # Motor SQLAlchemy async + sesiones
│   │   ├── auth.py                # JWT, hashing de PIN y contraseña
│   │   ├── rls.py                 # Row-Level Security multi-tenant
│   │   ├── rate_limiter.py        # Limitación de PIN/NFC/login
│   │   ├── pagination.py          # Helpers de paginación
│   │   ├── audit.py               # Registro de auditoría
│   │   ├── logging_config.py      # Logger JSON estructurado
│   │   ├── metrics.py             # Métricas Prometheus
│   │   ├── seed.py                # Datos semilla para desarrollo
│   │   ├── openapi_docs.py         # Personalización de OpenAPI
│   │   ├── models/                 # 23 modelos SQLAlchemy (tenant, employee, shift...)
│   │   └── routers/               # 19 routers (auth, clock, employees, billing...)
│   ├── alembic/                   # Migraciones de base de datos
│   ├── tests/                     # pytest (conftest.py, test_api.py, test_security.py)
│   ├── requirements.txt
│   ├── pytest.ini                 # asyncio_mode = auto
│   └── Dockerfile
│
├── frontend/                      # SPA vanilla JS + landing + PWA
│   ├── src/
│   │   └── app.js                  # Lógica principal de la SPA
│   ├── index.html                  # Dashboard SPA
│   ├── landing.html                # Landing pública
│   ├── design_system.css
│   ├── i18n.js                     # Internacionalización
│   ├── tests/                      # vitest (app.test.js, setup.js)
│   ├── e2e/                        # playwright (talentup.spec.cjs)
│   ├── package.json
│   └── vitest.config.js
│
├── hardware/                      # Firmware ESP32
│   ├── esp32_fichaje_cyd/         # Variante CYD 2432S028 (principal)
│   │   ├── src/
│   │   │   └── esp32_fichaje_cyd.ino
│   │   ├── test/
│   │   │   └── test_firmware.py   # Tests unitarios Python (mocks de hardware)
│   │   └── platformio.ini
│   └── esp32_fichaje/             # Variante legacy / referencia
│
├── .github/
│   └── workflows/
│       ├── ci.yml                 # CI principal (backend + firmware)
│       ├── backend-ci.yml         # CI backend avanzado (SQLite + PostgreSQL + Docker)
│       ├── deploy-backend.yml     # Deploy a Railway
│       └── deploy-frontend.yml   # Deploy a GitHub Pages
│
├── docs/                          # Documentación adicional
├── grafana/                       # Dashboards de observabilidad
├── .env.example                   # Plantilla de variables de entorno
├── docker-compose.yml             # PostgreSQL + Redis para desarrollo local
├── ROADMAP.md                     # Hoja de ruta del producto
├── TESTING.md                     # Guía detallada de testing
└── CONTRIBUTING.md                # Este archivo
```

### 4.1 Responsabilidad de cada capa

- **`backend/`**: Toda la lógica de negocio, validación, persistencia,
  autenticación, multi-tenancy (RLS), integración con Stripe y exportación
  de nóminas/reportes. 19 routers y 23 modelos SQLAlchemy.
- **`frontend/`**: Interfaz de usuario. SPA vanilla JS en `src/app.js` que
  consume la API. Sin framework, sin paso de build en producción (se sirve
  estático). Landing y PWA móviles incluidos.
- **`hardware/`**: Firmware para el dispositivo de fichaje físico basado en
  ESP32 CYD con lector NFC PN532. Se comunica con el backend vía HTTP.

---

## 5. Convenciones de commits

Usamos **Conventional Commits en español**. El formato es:

```
<tipo>([ámbito]): <descripción>

[cuerpo opcional]

[pie opcional]
```

### 5.1 Tipos permitidos

| Tipo | Significado | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(clock): permitir fichaje por QR` |
| `fix` | Corrección de bug | `fix(auth): corregir expiración de token en timezone` |
| `docs` | Solo documentación | `docs: añadir guía de contribución` |
| `style` | Formato, sangrado, puntos y comas (sin cambio de lógica) | `style(employees): normalizar comillas` |
| `refactor` | Refactor sin cambio de comportamiento | `refactor(database): extraer helper de sesión` |
| `perf` | Mejora de rendimiento | `perf(clock): indexar columna fichado_at` |
| `test` | Añadir o corregir tests | `test(api): cubrir aislamiento multi-tenant` |
| `chore` | Tareas de mantenimiento, deps, CI | `chore(deps): subir fastapi a 0.110` |
| `ci` | Cambios en CI/CD | `ci: añadir job de PostgreSQL en backend-ci` |
| `build` | Sistema de build o dependencias | `build(docker): optimizar capa de pip` |
| `revert` | Revertir un commit anterior | `revert: feat(billing) por fallo en webhook` |

### 5.2 Ámbitos (`scope`) recomendados

Los ámbitos reflejan los módulos del backend y las áreas del proyecto:

- **Routers backend**: `auth`, `clock`, `employees`, `shifts`, `schedules`,
  `calendar`, `holidays`, `leave`, `vacations`, `payroll`, `overtime`,
  `incidents`, `billing`, `notifications`, `devices`, `tenants`, `reports`,
  `settings`, `contracts`
- **Infraestructura**: `database`, `rls`, `rate-limit`, `audit`, `logging`,
  `metrics`, `openapi`
- **Frontend**: `frontend`, `landing`, `pwa`, `i18n`, `dashboard`
- **Firmware**: `firmware`, `nfc`, `tft`, `ota`
- **CI/CD**: `ci`, `deploy`, `docker`
- **General**: omite el ámbito si el cambio es transversal (`docs:` sin ámbito)

### 5.3 Reglas de redacción

1. **Idioma**: la descripción va en **español de España**. Ejemplos válidos:
   `feat(clock): añadir endpoint de fichaje masivo`, `fix(payroll): corregir
   cálculo de horas extra en turnos partidos`.
2. **Tono imperativo**: "añade", "corrige", "elimina", "refactoriza" — no
   "añadido" ni "añadiendo".
3. **Minúsculas** en el primer carácter de la descripción, sin punto final.
4. **Máximo 72 caracteres** en la línea de asunto.
5. **Cuerpo**: líneas de máximo 72 caracteres, explica el *qué* y el *porqué*,
  no el *cómo* (el diff ya lo muestra).
6. **Pie**: referencia issues o breaking changes. Usa `Closes #123`,
  `Fixes #456`, `Refs #789` o `BREAKING CHANGE:` para cambios rotundos.

### 5.4 Ejemplos completos

```
feat(billing): integrar webhooks de Stripe para suscripciones

Añade el router /billing/webhook que valida la firma HMAC de Stripe
y procesa los eventos checkout.session.completed e invoice.paid.
Actualiza el plan del tenant y registra el pago en billing_record.

Closes #142
```

```
fix(rls): filtrar empleados por tenant_id en listado

El endpoint GET /employees no aplicaba el filtro de tenant cuando
el usuario era manager, lo que permitía ver empleados de otros
tenants. Ahora se inyecta tenant_id desde el JWT en todas las
consultas.

Fixes #87
```

```
test(api): ampliar cobertura de aislamiento multi-tenant

Añade 6 tests que verifican que un owner de Tenant A no puede
acceder a recursos de Tenant B vía API (empleados, turnos,
vacaciones y fichajes). Cobertura de test_security sube a 92%.
```

---

## 6. Flujo de trabajo con Git

### 6.1 Sincroniza tu fork

Antes de empezar a trabajar, mantén tu fork al día con `upstream`:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

### 6.2 Crea una rama

Nunca trabajes directamente sobre `main`. Crea una rama descriptiva con el
formato `<tipo>/<ámbito>-<descripción-corta>`:

```bash
git checkout -b feat/clock-fichaje-qr
git checkout -b fix/auth-token-expiracion
git checkout -b docs/guia-contribucion
git checkout -b test/api-aislamiento-multi-tenant
```

### 6.3 Commits frecuentes y atómicos

Haz commits pequeños y enfocados. Un commit = un cambio lógico. Si tu PR
toca tres cosas distintas, son tres commits (o tres PRs).

```bash
git add backend/app/routers/clock.py
git commit -m "feat(clock): permitir fichaje por QR"
```

### 6.4 Rebase antes de enviar

Si tu rama se queda atrás de `main`, haz rebase para mantener un historial
limpio:

```bash
git fetch upstream
git rebase upstream/main
# Resuelve conflictos si los hay y continúa:
git rebase --continue
git push --force-with-lease origin feat/clock-fichaje-qr
```

Usa siempre `--force-with-lease` en lugar de `--force` para no sobrescribir
el trabajo de otras personas que puedan estar usando tu rama.

---

## 7. Proceso de Pull Request

### 7.1 Antes de abrir el PR

- [ ] Tu rama está actualizada con `main` (`git rebase upstream/main`).
- [ ] Los tests pasan localmente (ver [§8 Testing](#8-testing)).
- [ ] El código sigue las convenciones de estilo (ver [§9](#9-estilo-de-código)).
- [ ] El commit message sigue Conventional Commits en español.
- [ ] Si añades una funcionalidad nueva, hay tests que la cubren.
- [ ] Si changes la API o el esquema de base de datos, documentas el cambio
      en `CHANGELOG.md` o en el cuerpo del PR.
- [ ] Si tu cambio afecta al frontend, los tests de vitest y (si procede)
      playwright pasan.

### 7.2 Plantilla de PR

Copia esta plantilla en la descripción del PR:

```markdown
## Descripción

[Qué hace este PR y por qué. Máximo 3 párrafos.]

## Tipo de cambio

- [ ] Bug fix (cambio que corrige un issue)
- [ ] Nueva funcionalidad
- [ ] Cambio rotundo (breaking change)
- [ ] Refactor
- [ ] Documentación
- [ ] Test
- [ ] CI/CD

## Checklist

- [ ] Mi código sigue el estilo del proyecto
- [ ] He añadido tests que cubren mi cambio
- [ ] Todos los tests pasan localmente
- [ ] He actualizado la documentación relevante
- [ ] El commit message sigue Conventional Commits

## Issues relacionados

Closes #XXX
Refs #YYY
```

### 7.3 Revisión

1. **Auto-revisión**: revisa tu propio diff antes de pedir review. GitHub
   permite dejar comentarios en tu propio PR.
2. **Revisor asignado**: un maintainer revisará el PR. Espera feedback
   constructivo y responde con calma.
3. **Cambios solicitados**: haz los cambios en tu rama, haz commit y push.
   El PR se actualizará automáticamente. No cierres y abras un PR nuevo.
4. **Aprobación**: cuando un maintainer apruebe, hará el merge. Nosotros
   usamos **squash merge** por defecto para mantener un historial limpio.

### 7.4 Reglas de merge

- Se requiere **al menos una aprobación** de un maintainer.
- Los **checks de CI deben pasar** (tests en SQLite y PostgreSQL).
- El **título del PR** debe seguir Conventional Commits (se usa como mensaje
  de squash).
- **No se mergea con CI rojo**. Si un check es inestable, etiqueta el PR y
  avisa a un maintainer.

---

## 8. Testing

Toda contribución que cambie lógica de negocio debe incluir o actualizar tests.
El detalle exhaustivo está en [`TESTING.md`](./TESTING.md); aquí va el resumen
para contribuir de forma rápida.

### 8.1 Backend — pytest

```bash
cd backend

# Tests rápidos en SQLite (en memoria)
DATABASE_URL="sqlite+aiosqlite://" pytest --tb=short -q

# Tests con cobertura
DATABASE_URL="sqlite+aiosqlite://" pytest --cov=app --cov-report=term-missing

# Tests en PostgreSQL (requiere docker-compose)
docker compose up -d db
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/talentup_test" \
  pytest tests/ --tb=short -q
docker compose down
```

Configuración: `backend/pytest.ini` define `asyncio_mode = auto`. El
`conftest.py` proporciona fixtures (`client`, `seed_data`, `db_session`) que
crean la base de datos en memoria y datos semilla antes de cada test.

### 8.2 Frontend — vitest

```bash
cd frontend

# Tests unitarios
npm test            # equivale a: npx vitest run

# Modo watch durante desarrollo
npx vitest
```

Los tests viven en `frontend/tests/app.test.js` y cubren la lógica de
`src/app.js` con entorno jsdom.

### 8.3 Frontend — Playwright (e2e)

```bash
cd frontend

# Requiere backend en :8000 y frontend en :3000 corriendo
npx playwright test

# Modo interactivo (UI)
npx playwright test --ui

# Un solo archivo
npx playwright test e2e/talentup.spec.cjs
```

### 8.4 Firmware — PlatformIO / pytest

```bash
cd hardware/esp32_fichaje_cyd

# Tests unitarios Python (mocks de hardware, sin dispositivo real)
python -m pytest test/ -q

# Compilación (valida que el firmware build)
pio run
```

### 8.5 Cobertura mínima

No hay una puerta de cobertura estricta en CI todavía, pero se espera que
los PRs que añaden lógica de backend mantengan o suban la cobertura. El CI
sube el reporte de cobertura a Codecov automáticamente.

---

## 9. Estilo de código

### 9.1 Python (backend)

- **Formateador**: se recomienda `black` (configuración por defecto, línea de
  88 caracteres).
- **Importes**: usa `isort` con perfil `black`.
- **Tipado**: el backend usa type hints de Python 3.11 (`str | None`,
  `list[Employee]`, etc.). Pydantic v2 para validación.
- **Async**: toda la capa de base de datos es async (`async def`, `await`).
  No uses funciones síncronas de SQLAlchemy en los routers.
- **Nomenclatura**:
  - `snake_case` para funciones, variables y módulos.
  - `PascalCase` para clases (modelos, schemas).
  - `UPPER_SNAKE` para constantes.
- **Docstrings**: estilo Google o reStructuredText en funciones públicas y
  routers. Mínimo una línea descriptiva por endpoint.

### 9.2 JavaScript (frontend)

- **Sin framework**: vanilla JS. No se introduce React, Vue, Svelte ni ningún
  bundler. El frontend se sirve como ficheros estáticos.
- **ES2022+**: se permiten `async/await`, optional chaining (`?.`), nullish
  coalescing (`??`), top-level await donde aplique.
- **Módulos**: usa ES modules (`import`/`export`). El `package.json` declara
  `"type": "module"`.
- **Nomenclatura**:
  - `camelCase` para variables y funciones.
  - `PascalCase` para clases.
  - `kebab-case` para nombres de fichero de módulos.
- **Sin dependencias de runtime**: el frontend de producción no debe añadir
  dependencias en `dependencies` de `package.json`. Solo `devDependencies`
  para tests (vitest, playwright, jsdom).

### 9.3 C++ / Arduino (firmware)

- **Estilo Arduino** convencional con `snake_case` para funciones.
- **Constantes** en `UPPER_SNAKE` definidas con `#define` o `constexpr`.
- **Comentarios** en español explicando la lógica de negocio del fichaje
  (no la sintaxis de C++).

### 9.4 Markdown y documentación

- **Idioma**: español de España, con partes en inglés técnico cuando sea
  estándar (nombres de funciones, endpoints, flags de CLI).
- **Línea de máximo 80 caracteres** en prosa para legibilidad en diffs.
- **Tablas** para información estructurada (versiones, estados, comparativas).
- **Enlaces relativos** a otros documentos del repo (`[TESTING](./TESTING.md)`),
  no absolutos, salvo que apunten a GitHub.

---

## 10. Despliegue y entornos

### 10.1 Entornos

| Entorno | Backend | Frontend | Base de datos |
|---------|---------|----------|---------------|
| **local** | `uvicorn --reload` en `:8000` | `npx serve` en `:3000` | SQLite (`talentup_fichaje.db`) o PostgreSQL via docker-compose |
| **staging** | Railway (preview) | Vercel preview | PostgreSQL Railway |
| **producción** | Railway | Vercel (`talentup.es`) + GitHub Pages | PostgreSQL Railway + Redis |

### 10.2 Variables de entorno

Copia `.env.example` a `.env` y rellena los valores. Las críticas son:

- `DATABASE_URL`: cadena SQLAlchemy async. SQLite local o PostgreSQL.
- `JWT_SECRET`: secreto para firmar tokens. **Nunca se commitea**.
- `PIN_HASH_SALT`: sal para hashing de PINs de empleados.
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`: integración de pagos.
- `REDIS_URL`: colas, caché y rate-limiting distribuido.

`.env` está en `.gitignore` y `.dockerignore`. No lo subas nunca.

### 10.3 Migraciones (Alembic)

Los cambios de esquema se gestionan con Alembic. Si tu PR modifica modelos,
genera una migración:

```bash
cd backend
alembic revision --autogenerate -m "añadir columna geofence a employees"
alembic upgrade head          # aplica la migración localmente
git add alembic/versions/     # commitea el fichero generado
```

Las migraciones deben ser **reversibles** (define `downgrade`). El CI de
PostgreSQL ejecuta `alembic upgrade head` antes de correr los tests.

---

## 11. Roadmap y prioridades

El roadmap vivo está en [`ROADMAP.md`](./ROADMAP.md). Antes de empezar una
funcionalidad nueva, revisa el roadmap para no duplicar trabajo y alinearte
con las prioridades del producto.

### 11.1 Estado actual (resumen)

- **Backend**: 19 routers, 23 modelos, 64 tests en SQLite. Cobertura de
  seguridad alta. Pendiente: tests en PostgreSQL, tests de billing/payroll.
- **Frontend**: SPA en producción, design system v2, landing y PWA v2
  pendientes de publicar. Dashboard sin estilizar.
- **Firmware**: CYD completo (TFT_eSPI + PN532 + OTA), 911 líneas, compila
  en CI. Pendiente: flasheo en dispositivo real y provisioning.
- **Deploy**: Railway + Vercel + GitHub Pages. Pendiente: secrets reales,
  PostgreSQL y Redis en producción.

### 11.2 Cómo priorizamos

1. **Bugs de seguridad** y pérdida de datos → máxima prioridad.
2. **Aislamiento multi-tenant** (RLS) → siempre prioridad alta.
3. **Cumplimiento normativo** (RD-ley 8/2019) → prioridad alta.
4. **Funcionalidades del roadmap** con `effort` y dependencias claras.
5. **Mejoras de DX** (tests, docs, CI) → bienvenidas en cualquier momento.

---

## 12. Contacto y soporte

- **Issues**: abre un issue en GitHub para bugs, propuestas de funcionalidad
  o preguntas técnicas. Usa las plantillas si están disponibles.
- **Discusiones**: usa GitHub Discussions (si está habilitado) para preguntas
  abiertas, diseño de arquitectura o debate técnico largo.
- **Maintainers**: revisa los `CODEOWNERS` (si existe) o los colaboradores
  del repositorio para saber a quién pedir review.
- **Seguridad**: para reportar vulnerabilidades de forma privada, contacta
  con los maintainers directamente. No abras un issue público para
  vulnerabilidades de seguridad.

---

## Agradecimientos

Gracias a todas las personas que contribuyen a TalentUP Fichaje. Cada PR,
issue, revisión y discusión hace que el producto sea mejor para los equipos
de hostelería que dependen de él. Tu tiempo y experiencia son valorados.

---

*Documento mantenido por el equipo de TalentUP Fichaje. Última actualización:
agosto 2026. Si encuentras un error o algo desactualizado en esta guía, abre
un PR con el cambio — esta guía también es código abierto.*