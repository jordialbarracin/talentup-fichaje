# ROADMAP — TalentUP Fichaje v1.0

**Fecha:** 09 Aug 2026 · **Tag:** `v1.0.0` · **Ventana:** 6 semanas

> *Roadmap v2 falló: sin camino crítico claro, effort poco realista. Esta versión corrige con lista priorizada, effort S/M/L, semanas y dependencias explícitas.*

---

## 0. Estado actual

SaaS de fichaje para hostelería: **FastAPI + SPA vanilla JS + ESP32 CYD NFC**, multi-tenant, cumple RD-ley 8/2019.

| Capa | Avance | Bloqueador |
|------|--------|------------|
| **Backend** | 19 routers, 23 modelos, 64 tests (solo SQLite), Stripe, Grafana. Score 84/100 | Tests no corren en PG · billing/payroll sin tests · Stripe en dev |
| **Frontend** | SPA en prod · design system v2 + dashboard_structure.html (915 líneas) **sin estilos** · landing y PWA v2 **untracked** | Dashboard sin estilizar · no conectado a API |
| **Hardware** | Firmware CYD completo (TFT_eSPI + PN532 + OTA, 911 líneas). Compila en CI | **No flasheado en dispositivo real** · sin provisioning |
| **Deploy** | Railway (backend) + Vercel (`talentup.es`) + GitHub Pages (duplicado) | Secrets son placeholders · sin PG ni Redis |
| **Marketing** | Landing con SEO/JSON-LD/pricing | Sin Ads · sin reviews · sin demo · landing v2 sin publicar |

**Distancia a v1.0:** ~6 semanas con 1 dev + cron Sonnet a las 3:15 AM para fixes y estilización del dashboard.

---

## 1. "Done" v1.0

**Primera versión vendible y cobrable:**

1. Restaurante se registra, paga (Stripe live), configura tenant y ficha en < 30 min.
2. Dashboard funciona end-to-end con datos reales de la API.
3. Terminal NFC flasheado en CYD físico, fichaje online + offline verificado.
4. Reportes PDF/Excel cumplen RD-ley 8/2019 (inmutable, exportable, 4 años).
5. ≥ 1 beta-tester validado (pagando o en trial de 14 días).
6. Landing v2 + signup self-serve en `talentup.es`.
7. CI verde en `master` con tests en PostgreSQL.

**Excluido de v1.0:** app móvil nativa, integraciones nóminas externas, multi-idioma CA/EN en dashboard, geofencing, marketplace.

---

## 2. Hitos (6 semanas)

| Hito | Semana | Criterio de salida |
|------|--------|--------------------|
| **M1 — Dashboard usable** | S1 | `dashboard_structure.html` estilizado, responsive, commiteado. |
| **M2 — Backend production-ready** | S2–S3 | Fixes auditoría + tests PG + Stripe live. |
| **M3 — Integración frontend↔backend** | S3–S4 | Dashboard lee/escribe API real. Login, empleados, fichajes, reportes. |
| **M4 — Hardware beta** | S4–S5 | CYD flasheado en local real, fichaje E2E con backend prod. |
| **M5 — Go-live + 3 beta-testers** | S5–S6 | Landing publicada, signup activo, 3 trials pagando. |

---

## 3. Backlog priorizado

**Effort:** S = 1–2 días · M = 3–5 días · L = 1–2 semanas.

### 3.1 Backend — Semanas 1–3

| # | Tarea | Effort | Sem. | Notas |
|---|-------|--------|------|-------|
| B1 | **Tests en PostgreSQL (testcontainers)** | M | S2–S3 | Los 64 tests solo corren en SQLite. Añadir job CI con PG: JSONB, migraciones, concurrencia. Sin esto no se deploya en PG con confianza. |
| B2 | **Tests: billing, payroll, concurrencia** | M | S3 | 0 tests de billing y payroll. Sin esto no se cobra con confianza. |
| B3 | **Stripe live: Price IDs + webhook prod** | S | S3 | `_get_price_id()` usa placeholders dev. Configurar `STRIPE_PRICE_*` en Railway. |
| B4 | **Payroll close: paginación en BD** | S | S2 | `payroll.py` carga `.all()`. Migrar a `paginate()` si > 500 empleados. |
| B5 | **Limpiar `clock.py` rate limiter** | S | S2 | Eliminar stores locales duplicados. Delegar a `rate_limiter.py`. |
| B6 | **Migración Alembic: JSON → JSONB** | S | S3 | Audit logs usan `sa.JSON()`; debería ser `JSONB` para indexar en PG. |
| B7 | **Health check + readiness Railway** | S | S3 | Endpoint `/health` con ping a PG + Redis. |

**Effort total: ~4.5 sem-dev** (paralelizable a ~3 sem con cron asistido).

### 3.2 Frontend — Semanas 1–4

| # | Tarea | Effort | Sem. | Notas |
|---|-------|--------|------|-------|
| F1 | **Estilizar `dashboard_structure.html`** | **L** | S1 | **🔴 Bloqueante.** Esqueleto (915 líneas, 7 páginas) sin `<style>`. **Cron Sonnet 3:15 AM ataca esto cada noche.** |
| F2 | **Commitear frontend v2** | S | S1 | `design_system.css`, `dashboard_structure.html`, `sw_v2.js`, iconos, `landing_new.html` — todo untracked. |
| F3 | **Conectar dashboard a API real** | **L** | S3–S4 | Hoy es estático. Fetch a `/api/*` con JWT, loading/error/empty. **Convierte el producto en vendible.** |
| F4 | **Alinear páginas con `app.js`** | M | S2 | El dashboard usa nombres distintos a los que `app.js` espera. Alinear IDs. |
| F5 | **Login + registro self-serve** | M | S3 | Login con `/api/auth/*`. Registro → Stripe Checkout (trial 14 días). |
| F6 | **Activar PWA v2** | S | S4 | Reemplazar `sw.js`/`manifest.json` con v2. Verificar cola offline IndexedDB. |
| F7 | **Publicar `landing_new.html` como `/`** | S | S4 | Reemplazar `landing.html` raíz. Actualizar `vercel.json`. Verificar SEO. |

**Effort total: ~4.5 sem-dev** (F1 + F3 son los grandes; F1 automatizado con cron nocturno).

### 3.3 Hardware — Semanas 4–5

| # | Tarea | Effort | Sem. | Notas |
|---|-------|--------|------|-------|
| H1 | **Flashear CYD físico + smoke test** | S | S4 | Compila en CI pero **no flasheado en CYD real**. Verificar TFT, PN532, POST a backend. |
| H2 | **Provisioning de dispositivos** | M | S4–S5 | Falta pairing: el CYD debe obtener `tenant_id` + `device_token` al arrancar. |
| H3 | **Modo kiosco + PIN admin de salida** | M | S5 | El terminal no debe salir sin PIN de admin. Bloqueo fullscreen. |
| H4 | **Kit físico: BOM + proveedor** | M | S5 | CYD + soporte 3D + 10 tarjetas NTAG213. No bloquea v1.0 software (modo PIN/QR). Externalizable. |
| H5 | **OTA en producción** | S | S5 | No probado con backend en Railway. Verificar rotación de `FIRMWARE_OTA_TOKEN`. |
| H6 | **NFC E2E: tarjeta → CYD → backend → dashboard** | M | S5 | Flujo completo: acercar tarjeta → POST `/api/clock/nfc` → dashboard. **Valida la promesa central.** |

**Effort total: ~3.5 sem-dev** (H2, H4 e H6 son los más caros; H4 externalizable).

### 3.4 Deploy — Semanas 2–5

| # | Tarea | Effort | Sem. | Notas |
|---|-------|--------|------|-------|
| D1 | **Resolver Vercel vs GitHub Pages** | S | S2 | Decidir uno (Vercel — dominio `talentup.es`) y desactivar el otro. Evita SEO duplicado. |
| D2 | **Secrets de producción en Railway** | S | S3 | Configurar `JWT_SECRET`, `DATABASE_URL`, `REDIS_URL`, `STRIPE_*`, `CORS_ORIGINS`. Hoy placeholders. |
| D3 | **PostgreSQL gestionada (Supabase)** | S | S3 | Migrar de SQLite a Supabase (UE, RGPD). `alembic upgrade head`. Verificar RLS. |
| D4 | **Redis gestionado (Upstash)** | S | S3 | Sin Redis, el rate limiting cae a fallback en memoria (no distribuido). |
| D5 | **CI: job PostgreSQL + coverage gate** | M | S3 | Matrix con PG en GitHub Actions. Coverage ≥ 70% en routers críticos (auth, clock, billing). |
| D6 | **Monitoreo + alertas Grafana** | M | S4 | Error rate > 1%, p95 > 500ms, caída de health check. |
| D7 | **Backup automático de PG** | S | S5 | Snapshot diario en Supabase. RGPD: 4 años. |

**Effort total: ~2.5 sem-dev** (mucho es configuración, paralelizable).

### 3.5 Marketing — Semanas 4–6

| # | Tarea | Effort | Sem. | Notas |
|---|-------|--------|------|-------|
| M1 | **Publicar landing v2 en `talentup.es`** | S | S4 | `landing_new.html` lista pero untracked. Commitear, deployar, verificar SEO. |
| M2 | **Signup + trial self-serve** | M | S4–S5 | "Probar gratis" → registro → Stripe Checkout (trial 14 días) → onboarding. |
| M3 | **Email de onboarding** | S | S5 | Conectar a Resend. Secuencia: bienvenida → día 3 → día 7 → día 14. |
| M4 | **Demo video + screenshots** | M | S5 | 90 segundos: dashboard + fichaje NFC. Sin esto, conversión baja. |
| M5 | **Outbound: 20 restaurantes** | M | S5–S6 | Hostelería en zona (Alicante/Murcia). Llamada + email. Objetivo: 3 trials. |
| M6 | **Google My Business + reviews** | S | S6 | Ficha de Google, 3-5 reviews de beta-testers. |
| M7 | **Google Ads (piloto)** | M | S6 | 500 €, 2 semanas, keywords "fichaje digital hostelería". Medir CAC. |

**Effort total: ~3 sem-dev** (parte no-técnico: ventas, video).

---

## 4. Resumen

| Categoría | Tareas | Effort total | Semanas |
|-----------|--------|--------------|---------|
| Backend | 7 | ~4.5 sem-dev | S1–S3 |
| Frontend | 7 | ~4.5 sem-dev | S1–S4 |
| Hardware | 6 | ~3.5 sem-dev | S4–S5 |
| Deploy | 7 | ~2.5 sem-dev | S2–S5 |
| Marketing | 7 | ~3 sem-dev | S4–S6 |
| **Total** | **34** | **~18 sem-dev** | **6 semanas calendario** |

**Camino crítico:** F1 (estilizar dashboard) → F3 (conectar API) → F5 (login/signup) → M2 (trial self-serve). Todo lo demás se paraleliza.

**Cron asistido:** Sonnet 3:15 AM ataca F1 cada noche sobre `dashboard_structure.html`. Resultados commiteados al amanecer.

---

## 5. Riesgos y mitigación

| Riesgo | Impacto | Prob. | Mitigación |
|--------|---------|-------|------------|
| `app.js` no encaja con el dashboard | Alto | Alta | F4 alinea IDs y rutas; presupuesto M, no L. |
| Stripe live rompe el checkout | Alto | Media | F5 en staging; webhook con `stripe listen` antes de prod. |
| PG diverge de SQLite en tests | Alto | Alta | B1 (testcontainers) antes de deploy prod. |
| Hardware no llega a tiempo | Medio | Media | v1.0 en modo PIN/QR; kit NFC como upsell post-launch. |
| Conversión de landing < 2% | Medio | Alta | M4 (video) + M5 (outbound) compensan con canal directo. |
| Cron Sonnet no estiliza bien el dashboard | Alto | Media | Revisión manual cada mañana; iteración sobre el commit nocturno. |

---

## 6. Aceptación v1.0

- ✅ 34/34 tareas · CI verde con PG · `talentup.es` con landing v2 + signup
- ✅ Dashboard conectado a API real (login, empleados, fichajes, reportes)
- ✅ CYD flasheado, NFC E2E · ≥ 1 beta-tester con Stripe activo
- ✅ Reportes PDF/Excel cumplen RD-ley 8/2019 · Backups PG + alertas Grafana

---

*Hermes Agent · 09 Aug 2026 · Basado en `CLAUDE_HANDOFF.md`, `CHANGELOG_v2.md`, auditorías (score 84/100) e inspección del código real.*