# TalentUP Fichaje — Documento de Analytics

**Versión:** 1.0 · **Dominio:** talentup.es · **Hosting:** Vercel (frontend) + Railway/Supabase (backend)
**Alcance:** Landing, Pricing, Contacto, Términos, Privacidad, Dashboard, App de fichaje (móvil/PWA) y hardware NFC.

> Estado actual: **sin analítica instrumentada** (sin `gtag`, sin `@vercel/analytics`, sin capa de eventos de producto). Este documento define la implementación objetivo.

---

## 1. Objetivos

Medir, en tres capas complementarias, el comportamiento del usuario desde que **descubre** TalentUP hasta que **ficha y paga**:

1. **Adquisición y conversión web** (marketing) → **GA4**
2. **Rendimiento y experiencia de carga** (web vitals) → **Vercel Analytics**
3. **Uso del producto y eventos de negocio** (fichaje, retención, expansión) → **KDP** (Key Digital Product — capa de eventos propia sobre backend + Grafana)

El norte es el revenue: **MRR**, **churn** y **LTV/CAC**. Todo evento existe para alimentar esos tres números.

---

## 2. Arquitectura de medición (3 pilares)

| Pilar | Herramienta | Qué mide | Dónde se instrumenta |
|-------|-------------|----------|---------------------|
| Marketing & conversión | **GA4** | Tráfico, funnel landing→pricing→contacto→trial, attribution de campañas | `<head>` de todas las páginas públicas |
| Rendimiento web | **Vercel Analytics + Speed Insights** | Core Web Vitals (LCP, CLS, INP), TTFB, visitas reales | Vercel dashboard + `@vercel/speed-insights` |
| Producto & negocio | **KDP** (eventos propios) | Fichajes, activación, uso de features, retención, churn, MRR | Backend FastAPI → PostgreSQL → Grafana |

Los tres sistemas comparten un **`tenant_id`** (empresa) y un **`anonymous_id`** (cookie `_tu`) que permite coser la identidad anónima del visitante con el usuario registrado tras el signup.

---

## 3. GA4 — Google Analytics 4

### 3.1 Setup
- **Property ID:** `talentup-es` (web stream único, dominio `talentup.es`).
- **Tag:** `gtag.js` cargado con **consentimiento** (Consent Mode v2, modo región `ES`).
- **Consentimiento:** banner RGPD en `landing.html` que lanza `gtag('consent','update',...)` al aceptar. Por defecto `denied` para `ad_storage` y `analytics_storage`.
- **Cross-domain:** no aplica (dominio único).
- **Enhanced Measurement:** activado (scroll, outbound clicks, site search, video engagement, file download).

### 3.2 Eventos personalizados a trackear (marketing)

| Evento GA4 | Trigger | Parámetros | Página |
|-----------|---------|------------|--------|
| `page_view` | automático Enhanced Meas. | `page_title, page_location` | Todas |
| `cta_click` | click en CTA principal | `cta_id (navbar / hero / pricing / footer)` | Landing, Pricing |
| `pricing_view` | view del bloque de planes | `plans_visible (starter,pro,enterprise)` | Landing, Pricing |
| `plan_selected` | click en "Empezar" de un plan | `plan_name, plan_price` | Pricing |
| `trial_started` | envío del form de registro trial | `plan, source` | Contacto/Dashboard |
| `contact_submit` | envío del form de contacto | `form_type (sales / support), subject` | Contacto |
| `hardware_kit_view` | apertura del modal/bloque del kit 49€ | — | Landing |
| `faq_open` | apertura de cada `<details>` FAQ | `faq_id` | Pricing |
| `language_change` | cambio de idioma | `from_lang, to_lang` | Navbar |
| `legal_page_view` | view de Términos/Privacidad | `doc_type` | Términos, Privacidad |

### 3.3 Conversiones (marcadas como `mark_as_conversion`)
`trial_started` (conversión primaria), `contact_submit` (ventas), `plan_selected` (intención).

### 4. Audiences
- `trial_no_activate`: vio `trial_started` pero no disparó `first_clock_in` en KDP a 7 días.
- `pricing_no_trial`: vio pricing pero no inició trial (retargeting de campañas).
- `enterprise_intent`: abrió bloque Enterprise + scroll > 60%.

---

## 5. Vercel Analytics + Speed Insights

### 5.1 Setup
- Activar **Vercel Analytics** (tab "Analytics" del proyecto) — recolección server-side, sin cookies, compatible con RGPD sin consentimiento (anonimiza IP).
- Instalar `@vercel/speed-insights` en el frontend vanilla mediante snippet en `index.html`:
  ```html
  <script type="module" src="https://cdn.vercel-insights.com/v1/speed-insights.js" defer></script>
  ```
- Configurar `vercel.json` con el dominio `talentup.es` ya presente.

### 5.2 Qué mide (KPIs técnicos)
- **Core Web Vitals reales:** LCP, CLS, INP (percentiles p75).
- **TTFB** por ruta (`/`, `/pricing.html`, `/contacto.html`).
- **Top pages** por vistas y por poor-vital rate.
- **Audience:** país, dispositivo, navegador (sin PII).

### 5.3 Umbrales objetivo (p75)
| Métrica | Objetivo | Límite aceptable |
|--------|---------|------------------|
| LCP | < 2.5 s | < 4.0 s |
| CLS | < 0.10 | < 0.25 |
| INP | < 200 ms | < 500 ms |
| TTFB | < 0.8 s | < 1.8 s |

Si una ruta supera el límite aceptable, se abre issue de rendimiento y se audita contra `design_system.css` / imágenes `/public`.

---

## 6. KDP — Key Digital Product (eventos de producto)

Capa de eventos propia, persistida en PostgreSQL (`analytics_events` table) y visualizada en el Grafana existente. **No** depende de terceros: datos de negocio en primera mano, exportables y auditables (RGPD).

### 6.1 Esquema de evento
```json
{
  "event_id": "uuid",
  "tenant_id": "uuid | null",
  "user_id": "uuid | null",
  "anonymous_id": "_tu cookie",
  "event_name": "string",
  "event_category": "activation|usage|revenue|churn|hardware",
  "properties": { "plan": "pro", "feature": "incidencias", ... },
  "ts": "timestamp"
}
```

### 6.2 Catálogo de eventos KDP

| Evento | Categoría | Trigger | Propiedades clave |
|--------|-----------|---------|-------------------|
| `signup_completed` | activation | empresa crea cuenta | `plan, source, employees_imported` |
| `employee_invited` | activation | alta de empleado | `method (bulk/single)` |
| `first_clock_in` | activation | primer fichaje real del tenant | `method (nfc/pin/qr), delay_hours` |
| `clock_in` | usage | cada fichaje | `method, offline, geofence_ok` |
| `incident_created` | usage | incidencia auto-detectada | `type (retraso/ausencia/salida)` |
| `payroll_export` | usage | exportación PDF/Excel nómina | `format, period` |
| `feature_used` | usage | uso de módulo | `feature (turnos/vacaciones/extra/contratos)` |
| `plan_upgraded` | revenue | cambio de plan ascendente | `from_plan, to_plan, delta_mrr` |
| `plan_downgraded` | revenue | cambio descendente | `from_plan, to_plan, delta_mrr` |
| `payment_succeeded` | revenue | cobro Stripe OK | `amount, plan` |
| `payment_failed` | revenue | cobro fallido | `reason` |
| `trial_expired` | churn | fin de 14 días sin conversión | `plan` |
| `subscription_cancelled` | churn | baja activa | `plan, reason, age_months` |
| `hardware_connected` | hardware | ESP32 emparejado | `device_id, firmware` |
| `hardware_offline` | hardware | dispositivo caído > 10 min | `device_id, last_seen` |
| `ota_update` | hardware | firmware actualizado | `from_ver, to_ver, success` |

---

## 7. KPIs

### 7.1 KPIs de adquisición (GA4)
| KPI | Definición | Objetivo |
|-----|-----------|----------|
| Sesiones/mes | sesiones únicas en talentup.es | +15% MoM |
| Tasa conversión trial | `trial_started / sesiones` | ≥ 4% |
| CAC blended | gasto marketing / trials convertidos a pago | < 80€ |
| Tasa contacto→trial | `trial_started / contact_submit` | ≥ 30% |

### 7.2 KPIs de rendimiento (Vercel)
| KPI | Objetivo |
|-----|---------|
| LCP p75 | < 2.5 s |
| INP p75 | < 200 ms |
| % rutas con good vitals | ≥ 90% |

### 7.3 KPIs de producto (KDP)
| KPI | Definición | Objetivo |
|-----|-----------|----------|
| Activación | % tenants con `first_clock_in` en 7 días | ≥ 70% |
| DAU/WAU | usuarios que fichan / activos semana | ratio ≥ 0.6 |
| Fichajes/día/tenant | media de `clock_in` por empresa activa | > 8 |
| Retención D30 | tenants activos a 30 días | ≥ 85% |
| MRR | suma MRR de planes activos | +20% MoM |
| Churn mensual | `subscription_cancelled / activos` | < 5% |
| NRR | (MRR inicio + expansión − churn) / MRR inicio | ≥ 110% |
| ARPU | MRR / clientes activos | creciente (move up-plan) |
| Trial→paid | `payment_succeeded / trial_started` | ≥ 40% |
| Hardware attach rate | tenants con kit 49€ / total | ≥ 25% |
| Uptime fichaje | 1 − `hardware_offline` horas / total | ≥ 99.5% |

---

## 8. Funnel de conversión (GA4 + KDP)

```
Visitante → Pricing view → Plan selected → Trial started → Activated (first_clock_in) → Paid
  100%         ~45%        ~18%             ~7%            ~5% (70% act.)      ~4% (40% conv.)
```

Cada paso es una **propuesta de mejora**: el mayor cuello proyectado está entre `trial_started` y `activated` (onboarding). La métrica rectora de ese tramo es **Time-to-first-clock-in** (objetivo < 24 h).

---

## 9. Dashboard de métricas

### 9.1 Grafana (producto — KDP)
Reutilizar el dashboard `talentup_overview.json` y añadir un nuevo **"TalentUP — Growth & Revenue"** con paneles:

1. **MRR y NRR** (stat + timeseries) — `SELECT SUM(mrr) FROM subscriptions WHERE status='active'`.
2. **Activación D7** (gauge) — % tenants con `first_clock_in` ≤ 7 días.
3. **Funnel** (bar gauge) — signup → first_clock_in → paid.
4. **Churn mensual** (stat + alerta si > 5%).
5. **Uso de features** (stacked bar) — `feature_used` por módulo.
6. **Fichajes por método** (pie) — NFC vs PIN vs QR.
7. **Hardware health** (table) — dispositivos online/offline y firmware.

### 9.2 Looker Studio (marketing — GA4)
Conector nativo GA4 + hoja de cálculo de gasto de campañas (Meta/Google Ads):
- **Adquisición por canal** (orgánico, paid, directo, referral).
- **Funnel de conversión GA4** con los eventos de §3.2.
- **CAC y ROAS** por canal (uniendo gasto con trials/pagos).

### 9.3 Vercel Analytics (técnico)
- Vista **Web Analytics** (visitas, top pages, audience).
- Vista **Speed Insights** (web vitals por ruta + dispositivo).
- Alerta automática si LCP p75 > 4 s en `/` o `/pricing.html`.

---

## 10. RGPD y consentimiento

- **GA4** se carga con Consent Mode v2, región `ES`, estado inicial `denied`. Sin consentimiento no se envían eventos a Google (solo pings modeless).
- **Vercel Analytics** es server-side y anonimiza IP → no requiere consentimiento; se mantiene siempre activo (datos agregados, sin perfilado).
- **KDP** almacena eventos en PostgreSQL propio. Los datos de empleados (fichajes) ya están cubiertos por el DPA y la política de privacidad existentes. Los eventos de producto no contienen PII de empleados, solo `tenant_id` y agregados.
- Cookie `_tu` (anonymous_id): duración 12 meses, clasificada como "analytics", cubierta por el banner.

---

## 11. Roadmap de implementación

| Fase | Tarea | Esfuerzo |
|------|-------|----------|
| 1 | Añadir `gtag.js` + Consent Mode v2 + banner RGPD en landing/pricing/contacto/terminos/privacidad | 1 día |
| 2 | Crear eventos GA4 de §3.2 y conversiones | 0.5 día |
| 3 | Activar Vercel Analytics + Speed Insights en dashboard Vercel | 0.5 día |
| 4 | Backend: tabla `analytics_events` + endpoint `POST /api/events` (rate-limited, auth opcional) | 1 día |
| 5 | Frontend app: helper `track(event, props)` que envía a KDP (y replica a GA4 los compartidos) | 0.5 día |
| 6 | Dashboard Grafana "Growth & Revenue" + alertas | 1 día |
| 7 | Looker Studio conectado a GA4 + hoja de gasto | 0.5 día |
| 8 | Documentación interna + revisión trimestral de KPIs | continuo |

**Responsable:** producto + backend. **Revisión de KPIs:** primer lunes de mes, 30 min, frente al dashboard de Grafana.