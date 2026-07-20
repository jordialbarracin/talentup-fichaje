# Re-auditoría CTO — TalentUP Fichaje v3.1 (post-fixes 86 → ?)

**Fecha:** 2026-07-20  
**Auditor:** CTO Venture Studio (subagente Hermes)  
**Score anterior:** 86/100  
**Score actualizado:** 86/100  
**Diferencia:** 0 puntos

---

## Veredicto ejecutivo

**No, no llegamos a 88+.** El score se mantiene en **86/100**.

Se verificaron 6 puntos solicitados. La mayoría están **implementados**, pero dos de ellos aún tienen matices que impiden subir la puntuación y uno de ellos (deploy paths) está parcialmente roto. No se han introducido regresiones importantes, pero tampoco se ha cerrado suficiente deuda técnica como para justificar un salto a 88. La distancia a 90 sigue siendo de 3-5 días de trabajo enfocado.

---

## 1. Verificación punto por punto

| # | Fix claim | Estado real | Evidencia | Notas |
|---|-----------|-------------|-----------|-------|
| 1 | **/api/auth/refresh cookie-only** | ✅ Real | `backend/app/routers/auth.py:182-183` lee el refresh token **únicamente** de `request.cookies.get("refresh_token")`. No acepta body ni header. Si falta cookie → 401. | Correcto. La cookie se setea en login/register con `httponly=True`, `secure=True`, `samesite="lax"`. |
| 2 | **OpenAPI deshabilitado en prod** | ✅ Real | `backend/app/main.py:99-101` usa `docs_url`, `redoc_url`, `openapi_url` condicionales a `_is_production()`. En producción (`APP_ENV=production`) todos son `None`. | Sólo queda accesible en dev/staging. Bien. |
| 3 | **Stripe 403 fail-closed** | ✅ Real | `backend/app/routers/billing.py:181-183` devuelve **403** si `STRIPE_WEBHOOK_SECRET` está vacío. Firma ausente → 400, firma falsa → 400, secret configurado correctamente → firma. Sin `STRIPE_SECRET_KEY` el módulo `_get_stripe()` devuelve `None` y se devuelve 503, pero eso es **después** de comprobar el webhook secret. | El flujo fail-closed está operativo: un atacante no puede llegar a Stripe sin el secret. |
| 4 | **Frontend sin localStorage token** | ✅ Funcional | `frontend/index.html:1340-1347` lee la cookie `access_token` vía `getCookie()`. No aparece `localStorage.getItem('talentup_token')`, `setStoredToken` ni `removeStoredToken` en el código. Login y register usan la API y confían en las cookies httpOnly (`credentials: 'include'`). | El frontend ya no almacena ni lee token de localStorage. Inicialización también usa cookie. |
| 5 | **Deploy paths** | ⚠️ Parcial | `.github/workflows/deploy-backend.yml` ahora referencia `backend/Dockerfile` ✅. Sin embargo, `backend-ci.yml` todavía usa `context: ./backend` y `file: ./backend/Dockerfile`, que **no existen** (el Dockerfile está en la raíz `./Dockerfile` y otro en `./backend/Dockerfile`). Hay **dos Dockerfiles**: raíz (`./Dockerfile`) apunta a `backend/app`, y `./backend/Dockerfile` apunta a `app`. Ambos son válidos según contexto, pero los workflows no están coordinados. | Riesgo de build fallido en CI. Requiere unificar. |
| 6 | **docker-compose secrets** | ⚠️ Parcial | `docker-compose.yml` ya no tiene defaults hardcodeados para `POSTGRES_PASSWORD`, `JWT_SECRET`, `PIN_HASH_SALT` ✅. Pero sigue usando `environment:` en lugar de un `env_file` externo o Docker secrets, y no hay `.dockerignore`, por lo que una imagen de Docker puede empaquetar `.env` si se copia accidentalmente. | Mejor que antes, pero no es gestión de secretos real (no `secrets:` de Compose ni `env_file`). |

---

## 2. Bugs / inconsistencias encontrados durante la auditoría

### Bug A: Workflow `backend-ci.yml` apunta a Dockerfile inexistente
- `backend-ci.yml:84-85` usa `context: ./backend` y `file: ./backend/Dockerfile`.
- En el repositorio hay:
  - `./Dockerfile` (raíz, contexto raíz, copia `backend/app`).
  - `./backend/Dockerfile` (contexto `./backend`, copia `app`).
- `backend-ci.yml` fallará al no encontrar `./backend/Dockerfile` a menos que se use el de la raíz o se ajuste la ruta.

**Recomendación:** unificar en un único Dockerfile (recomendado `./backend/Dockerfile` con contexto `./backend`) y actualizar ambos workflows.

### Bug B: Sin `.dockerignore`
- No existe `.dockerignore` ni en raíz ni en `backend/`.
- Riesgo de incluir `.env`, `.git`, `node_modules`, `__pycache__`, `*.db` en la imagen de producción.

**Recomendación:** añadir `.dockerignore` en `./backend/`.

### Bug C: Logout frontend no limpia cookies
- `frontend/index.html:1646-1654` hace logout solo a nivel UI (`state.user = null`, muestra login).
- No llama a `/api/auth/logout` ni borra las cookies `access_token` / `refresh_token` del navegador.
- Esto significa que después de logout, las cookies httpOnly siguen presentes hasta que expiren (8h). En un entorno compartido es un riesgo.

**Recomendación:** añadir endpoint `POST /api/auth/logout` que expire las cookies, y llamarlo desde el frontend.

### Bug D: Tests no cubren cookies ni refresh
- `backend/tests/test_api.py` y `test_security.py` siguen usando `Authorization: Bearer <token>` directamente.
- No hay tests que validen que `POST /api/auth/login` setea cookies, ni que `/api/auth/refresh` rechaza sin cookie, ni que `get_current_user` lee cookie primero.
- El 64/64 sigue siendo robusto, pero no prueba el nuevo modelo de autenticación.

---

## 3. Score actualizado por dimensión

| Dimensión | Peso | Score anterior | Score actual | Δ | Justificación |
|---|---:|---:|---:|---:|:---|
| Backend FastAPI | 20% | 88 | 88 | 0 | Refresh cookie-only, OpenAPI prod off, Stripe fail-closed. Sin cambios mayores. |
| Base de Datos | 15% | 86 | 86 | 0 | Payroll ya pagina en BD (`paginate()`). Sin PostgreSQL en tests ni RLS. |
| Seguridad | 15% | 87 | 87 | 0 | Cookie-only auth real, PIN salt obligatorio, Stripe 403. CSP sigue con `style-src 'unsafe-inline'`. |
| Frontend/PWA | 10% | 70 | 71 | +1 | Frontend sin localStorage token. Penaliza logout sin limpiar cookies y monolito 3.3K líneas. |
| Tests | 10% | 88 | 87 | -1 | 64/64 pasan, pero no prueban cookies ni refresh. Sólo SQLite. |
| DevOps / Deploy | 10% | 74 | 76 | +2 | Deploy workflow apunta a ruta correcta, pero CI Docker roto y falta `.dockerignore`. |
| Multi-tenant / Scale | 10% | 72 | 72 | 0 | Sin RLS, aislamiento solo por app-layer. |
| Producto / Negocio | 10% | 80 | 80 | 0 | Viable para piloto controlado. |
| **Global ponderado** | | **86** | **86** | **0** | |

---

## 4. ¿Por qué no 88? Gaps para el siguiente salto

| Prioridad | Gap | Evidencia | Est. effort |
|---:|---|---|---|
| 🔴 | **Unificar Dockerfile y arreglar `backend-ci.yml`** | `backend-ci.yml:84-85` referencia `./backend/Dockerfile` inexistente; hay dos Dockerfiles en el repo. | 0.25 días |
| 🔴 | **Logout que limpie cookies** | `frontend/index.html:1646-1654` no borra cookies; falta `POST /api/auth/logout`. | 0.5 días |
| 🟠 | **Añadir `.dockerignore`** | No existe `.dockerignore` en raíz ni `backend/`. | 0.25 días |
| 🟠 | **Tests de cookie auth + refresh** | No hay tests que validen cookies httpOnly ni el flujo cookie-only de refresh. | 1 día |
| 🟠 | **PostgreSQL real en CI** | `backend/tests/conftest.py:11` fuerza SQLite. | 1-2 días |
| 🟠 | **RLS básico en PostgreSQL** | No existe `SET SESSION app.tenant_id` ni políticas. | 2 días |
| 🟢 | **CSP nonce real para frontend** | `style-src 'unsafe-inline'` residual; frontend estático no inyecta nonce. | 1 día |
| 🟢 | **Rate limiting registro en Redis limpio** | `backend/app/routers/auth.py:40-66` tiene lógica híbrida redundante. | 0.5 días |

---

## 5. Recomendaciones priorizadas para llegar a 90

1. **Arreglar CI/CD Docker** (0.25 días): unificar Dockerfile, corregir `backend-ci.yml`, añadir `.dockerignore`.
2. **Logout real con limpieza de cookies** (0.5 días): endpoint `POST /api/auth/logout` + llamada frontend.
3. **Tests de cookie auth** (1 día): validar login setea cookies, refresh rechaza sin cookie, acceso con cookie funciona.
4. **Job CI con PostgreSQL 16** (1-2 días): al menos un test de integración en PostgreSQL.
5. **RLS básico** (2 días): `tenant_id` column + policies + `set_config`.
6. **Tests E2E estables** (1-2 días): PWA y terminal requieren servidores adicionales; actualizar selectores.

---

## 6. Conclusión

**Score actualizado: 86/100. No se alcanza 88+.**

Los cuatro fixes de seguridad aplicados (refresh cookie-only, OpenAPI off en prod, Stripe 403 fail-closed, frontend sin localStorage token) son reales y mejoran la postura de seguridad del sistema. Sin embargo, la deuda técnica en DevOps (Dockerfile duplicado + CI roto), el logout incompleto, la ausencia de tests de cookie auth y la falta de RLS/PostgreSQL en CI impiden el salto a 88.

**Honestamente:** TalentUP Fichaje sigue siendo un piloto viable y seguro para producción controlada, pero necesita 2-3 días de trabajo enfocado en CI/CD, logout y tests para consolidar 88, y 4-5 días para aspirar a 90 con RLS y PostgreSQL en CI.
