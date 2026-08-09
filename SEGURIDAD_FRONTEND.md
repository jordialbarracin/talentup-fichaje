# Documento de Seguridad Frontend — TalentUP Fichaje

**Versión:** 1.0 · **Fecha:** 2026-08-09 · **Dominio:** `talentup.es`
**Alcance:** Landing, Pricing, Contacto, Dashboard, App de fichaje (PWA móvil + terminal NFC).
**Hosting:** Vercel (frontend estático) + Railway/Supabase (backend FastAPI).

> Este documento describe cómo se protege el frontend de TalentUP: Content Security Policy, CORS, prevención XSS, CSRF, rate limiting, almacenamiento de JWT y validación de inputs. Cada control se mapea a código real del repositorio.

---

## 1. Modelo de amenazas

El frontend de TalentUP es un conjunto de **páginas HTML estáticas** servidas por Vercel (sin build ni SSR). Las superficies expuestas son:

1. **Marketing / legales** — páginas públicas: `landing_new`, `pricing`, `contacto`, `terminos`, `privacidad`.
2. **App de gestión** — SPA de administrador: `dashboard_new.html` e `index.html`.
3. **PWA de fichaje** — `terminal/index.html` (kiosko NFC) y `mobile/index.html`.

Las amenazas relevantes son: **XSS almacenado**, **CSRF** sobre endpoints autenticados, **robo de JWT**, **fuerza bruta** sobre login y PIN, **inyección SQL** y **abuso de API** (DoS). La estrategia es **defensa en profundidad**: CSP + cookies httpOnly + escape en render + validación backend + rate limiting distribuido.

---

## 2. Content Security Policy (CSP)

La CSP se aplica en el **backend** mediante `SecurityHeadersMiddleware` (`backend/app/main.py`), no en meta tags del HTML. Esto garantiza que toda respuesta —incluida la servida por FastAPI— lleve la cabecera, y permite generar un **nonce criptográfico por petición** sin `unsafe-inline`.

```python
request.state.csp_nonce = secrets.token_urlsafe(16)
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
```

**Directivas clave:**

| Directiva | Valor | Propósito |
|---|---|---|
| `default-src` | `'self'` | Deniega todo por defecto; sólo el propio origen carga recursos. |
| `script-src` | `'self' 'nonce-{nonce}' cdn.jsdelivr.net` | Bloquea scripts inline sin nonce y dominios arbitrarios. Permite CDN jsdelivr (iconos/charts). |
| `style-src` | `'self' 'nonce-{nonce}'` | Sin `unsafe-inline` residual. |
| `img-src` | `'self' data: blob:` | Permite avatares inline y blobs de FileReader. |
| `connect-src` | `'self'` | El frontend sólo puede `fetch` al propio backend; bloquea exfiltración a dominios externos. |
| `frame-ancestors` | `'none'` | Anti-clickjacking: la app no puede ser embebida en iframes. |
| `base-uri` | `'self'` | Evita secuestro del `<base href>`. |

**Cabeceras de seguridad complementarias** emitidas por el mismo middleware:

- `X-Content-Type-Options: nosniff` — bloquea MIME-sniffing.
- `X-Frame-Options: DENY` — refuerzo de `frame-ancestors 'none'` para navegadores legacy.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` — sólo en HTTPS (`X-Forwarded-Proto: https` o `APP_ENV=production`).

El helper `add_csp_nonce()` inyecta el nonce en etiquetas inline de respuestas HTML servidas por FastAPI, de modo que el frontend vanilla pueda mantener estilos y scripts inline sin `unsafe-inline`.

---

## 3. CORS

CORS se configura en el backend con `CORSMiddleware` y **lista blanca explícita de orígenes** desde la variable de entorno `CORS_ORIGINS`:

```python
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Decisiones de seguridad:**

- **No se usa `*`**: los orígenes se enumeran explícitamente. En producción `CORS_ORIGINS=https://talentup.es`.
- **`allow_credentials=True`**: necesario porque el frontend envía cookies httpOnly con `credentials: 'include'`. Esto fuerza a que `allow_origins` sea una lista explícita (no `*`).
- **Métodos restringidos**: sólo `GET, POST, PUT, PATCH, DELETE`; `TRACE` y `CONNECT` quedan fuera.
- **Cabeceras permitidas**: sólo `Authorization` y `Content-Type`.

---

## 4. Prevención de XSS

El XSS es la amenaza principal en un frontend vanilla que renderiza con `innerHTML`. TalentUP se defiende en **tres capas**:

### 4.1 Escape en el frontend (capa de render)

`dashboard_new.html` define una función de escape `esc()` y la aplica a **todo dato dinámico** antes de insertarlo en plantillas HTML:

```javascript
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c];
  });
}
// Uso: '<span class="emp-name">' + esc(e.nombre) + '</span>'
```

Todo campo de la API (nombres, emails, títulos de incidencias, descripciones) pasa por `esc()`. Los contadores internos usan `textContent` cuando no necesitan HTML.

### 4.2 Escape en el backend (capa de serialización)

Cada modelo SQLAlchemy sobrescribe la serialización aplicando `html.escape(str(value))` a los campos de texto antes de devolverlos al frontend:

```python
# backend/app/models/employee.py, incident.py, clock_in.py, contract.py, ...
def to_dict(self):
    return { "name": html.escape(str(self.name)), ... }
```

Esto produce **defensa en profundidad**: aunque el frontend olvidara escapar, el backend ya devolvería entidades HTML (`&lt;script&gt;`). La auditoría XSS (`xss_resp.json`) confirma que un payload `<script>alert(1)</script>` se almacena pero se serializa como `&lt;script&gt;...`.

### 4.3 CSP como tercera línea

Aunque `esc()` y `html.escape` neutralizan el XSS almacenado, la CSP cierra el hueco residual: `script-src` sin `unsafe-inline` bloquea la ejecución de scripts inyectados, y el nonce por petición impide reutilizar nonces capturados.

---

## 5. Protección CSRF

TalentUP no usa tokens CSRF tradicionales. La protección se basa en **cookies SameSite** combinadas con la **lista blanca CORS**:

- **`SameSite=Lax`** (por defecto): las cookies no se envían en peticiones cross-site POST (formularios de terceros). Sólo se envían en navegación top-level GET. Esto neutraliza CSRF clásico sobre endpoints de mutación.
- **CORS restrictivo**: un sitio atacante no puede leer la respuesta de una petición cross-origin porque su origen no está en `allow_origins`; y como las cookies son httpOnly + SameSite, tampoco puede adjuntarlas.

En entornos E2E (Playwright sobre HTTP) se permite relajar `COOKIE_SECURE=false` y `COOKIE_SAMESITE=none`, pero nunca en producción.

---

## 6. Rate Limiting

El rate limiting protege el frontend contra abuso de API y fuerza bruta. Se aplica en **dos capas**:

### 6.1 Middleware global (por IP + endpoint)

`RateLimitMiddleware` (`backend/app/rate_limit.py`) implementa ventana deslizante in-memory por par `(IP, endpoint_prefix)`:

| Endpoint | Límite | Ventana |
|---|---|---|
| `/api/auth/login` | 10 req | 60 s |
| `/api/clock` | 30 req | 60 s |
| `/api/clock/nfc` | 30 req | 60 s |
| `/api/employees` | 60 req | 60 s |
| Default (resto) | 100 req | 60 s |

Al superar el límite devuelve **429** con cabecera `Retry-After`.

### 6.2 Rate limiting de negocio (Redis-backed)

`rate_limiter.py` implementa límites específicos con **Redis** (fallback in-memory en dev):

- **Login**: 10 intentos fallidos por IP cada 5 min (los aciertos no consumen cuota).
- **Registro**: 3 por IP por hora.
- **PIN/NFC/QR clock**: 10 fichajes/min por `(IP, tenant_id)`.
- **Bloqueo de PIN**: tras 5 fallos de PIN/min, la IP queda bloqueada 5 minutos (`PIN_BLOCK_MINUTES=5`).
- **Límite por tenant**: 100 fichajes/hora por `tenant_id`, independiente de IP/método.

El backend lee la IP real detrás de proxy vía `X-Forwarded-For`.

**Refresh token con rotación**: `/api/auth/refresh` lee el token sólo de la cookie httpOnly, valida que no esté revocado (Redis con TTL 30 días), emite un nuevo access token y **revoca el refresh anterior**, permitiendo detectar robo.

---

## 7. Almacenamiento de JWT

**Decisión arquitectónica: el JWT nunca se persiste en `localStorage` ni `sessionStorage`.** Se gestiona mediante **cookies httpOnly**:

```python
# backend/app/routers/auth.py — login
response.set_cookie(
    key="access_token", value=access_token,
    httponly=True, secure=_COOKIE_SECURE, samesite=_COOKIE_SAMESITE,
    max_age=28800,  # 8h
)
response.set_cookie(
    key="refresh_token", value=refresh_token,
    httponly=True, secure=_COOKIE_SECURE, samesite=_COOKIE_SAMESITE,
    max_age=REFRESH_TOKEN_TTL_SECONDS,  # 30 días
)
```

**Propiedades:**

| Atributo | Valor | Motivo |
|---|---|---|
| `httponly` | `True` | JS no puede leer la cookie → inmunidad a robo por XSS. |
| `secure` | `True` (prod) | Sólo se envía sobre HTTPS. |
| `samesite` | `Lax` (prod) | Protección CSRF. |
| `max_age` access | 28800 s (8h) | Vida corta; `ACCESS_TOKEN_EXPIRE_MINUTES=480`. |
| `max_age` refresh | 30 días | Rotación: cada uso revoca el anterior. |

El backend lee el token **primero de la cookie**, con fallback al header `Authorization: Bearer`. El frontend hace `fetch` con `credentials: 'include'`, de modo que el navegador adjunta las cookies automáticamente sin exponer el token al código JS. `JWT_SECRET` es obligatorio en producción (falla al arrancar si falta); algoritmo `HS256`.

---

## 8. Validación de Inputs

### 8.1 Backend (Pydantic)

Todo input del frontend se valida con modelos Pydantic antes de tocar la lógica de negocio:

```python
class RegisterRequest(BaseModel):
    restaurant_name: str
    owner_name: str
    email: str
    password: str

    @field_validator("password")
    def password_min_length(cls, v):
        if len(v) < 6: raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v
    # ... validadores de no-vacío para restaurant_name y owner_name
```

### 8.2 Prevención de SQLi

Todas las consultas usan **SQLAlchemy ORM parametrizado** (`select(User).where(User.email == req.email)`). No hay concatenación de SQL. La auditoría confirma que pruebas de inyección devuelven 401 sin error de sintaxis.

### 8.3 Límite de tamaño de body

`BodySizeLimitMiddleware` rechaza peticiones con body > **1 MB** con **413**, protegiendo contra payloads maliciosos y DoS por memoria.

### 8.4 Frontend

El frontend valida formatos básicos antes de enviar, pero **nunca** confía en esta validación: el backend es la fuente de verdad. No se usa `eval`, `Function()` ni `document.write` en ningún punto del frontend.

---

## 9. Resumen de controles

| Control | Capa | Estado |
|---|---|---|
| CSP con nonce por petición | Backend middleware | ✅ Sin `unsafe-inline` |
| HSTS / X-Frame-Options / nosniff | Backend middleware | ✅ Prod |
| CORS lista blanca explícita | Backend middleware | ✅ |
| Cookies httpOnly + Secure + SameSite | Backend auth | ✅ |
| JWT fuera de localStorage | Arquitectura | ✅ |
| Refresh token con rotación y revocación | Backend auth | ✅ Redis |
| Escape `esc()` en render frontend | Frontend JS | ✅ |
| `html.escape` en serialización backend | Modelos | ✅ |
| Rate limiting global + por negocio | Backend middleware + Redis | ✅ |
| Validación Pydantic + SQLi parametrizado | Backend | ✅ |
| Límite de body 1 MB | Backend middleware | ✅ |

**Score de seguridad global: 84/100** (auditoría interna). Riesgo residual: webhook de Stripe sin fail-closed estricto cuando falta configuración (fuera del alcance frontend).