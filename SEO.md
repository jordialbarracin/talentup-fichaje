# Documento SEO — TalentUP Fichaje

> Estrategia de indexación, keywords, metadatos, structured data, sitemap y robots para cada página del sitio `talentup.es`.
> Dominio canónico: `https://talentup.es` (redirección 301 permanente de `www.talentup.es` y de `/landing.html` → `/`).
> Idioma: `es-ES`. Mercado: España. Sector: hostelería / control horario.
> Última revisión: 2026-08-09.

---

## 1. Inventario de páginas y estrategia de indexación

| # | Página | URL canónica | Indexable | Prioridad | Frecuencia |
|---|--------|--------------|----------|----------|------------|
| 1 | Landing (inicio) | `https://talentup.es/` | Sí | 1.0 | Semanal |
| 2 | Precios | `https://talentup.es/pricing.html` | Sí | 0.9 | Mensual |
| 3 | Contacto | `https://talentup.es/contacto.html` | Sí | 0.7 | Mensual |
| 4 | Términos | `https://talentup.es/terminos.html` | Sí | 0.3 | Anual |
| 5 | Privacidad | `https://talentup.es/privacidad.html` | Sí | 0.3 | Anual |
| 6 | Dashboard (app) | `https://talentup.es/dashboard_new.html` | No | — | — |
| 7 | App móvil (PWA) | `https://talentup.es/mobile/` | No | — | — |
| 8 | Terminal NFC | `https://talentup.es/terminal/` | No | — | — |
| 9 | Offline | `https://talentup.es/offline.html` | No | — | — |
| 10 | API | `https://talentup.es/api/*` | No | — | — |

Las páginas 6–10 son **privadas** (detrás de login o sin valor SEO) y se bloquean en `robots.txt` con `Disallow`. El dashboard, el móvil y el terminal contienen datos de clientes y no deben indexarse.

---

## 2. Keywords por página

### Landing (`/`)
**Primarias:** control horario hostelería, fichaje digital, control de presencia, registro horario restaurante.
**Secundarias:** fichaje NFC, fichaje offline, nóminas automáticas, gestión de turnos, terminal fichaje, app fichaje empleados.
**Long-tail:** control horario hostelería RGPD, fichaje digital sin hardware, software fichaje restaurante, control jornada RD-ley 8/2019, fichaje offline wifi caído, terminal NFC fichaje empleados.
**Intención:** transaccional-informacional. Competidores: Kenjo, BizneoHR, Sesame HR, WorkMeter.

### Precios (`/pricing.html`)
**Primarias:** precios control horario, planes fichaje digital, tarifa software fichaje.
**Secundarias:** fichaje hostelería precio, control horario SaaS coste, plan starter pro enterprise.
**Long-tail:** cuánto cuesta control horario hostelería, fichaje digital barato, control presencia sin permanencia.
**Intención:** transaccional. Alta conversión.

### Contacto (`/contacto.html`)
**Primarias:** contacto TalentUP, soporte fichaje digital, soporte técnico control horario.
**Secundarias:** atención comercial hostelería, demo control horario.
**Long-tail:** cómo contactar TalentUP Fichaje, formulario contacto software fichaje.
**Intención:** navegacional.

### Términos (`/terminos.html`)
**Primarias:** términos servicio TalentUP, condiciones uso fichaje digital.
**Secundarias:** contrato SaaS hostelería, propiedad intelectual software fichaje.
**Long-tail:** términos servicio control horario, condiciones B2B SaaS fichaje.
**Intención:** informativa-legal.

### Privacidad (`/privacidad.html`)
**Primarias:** política privacidad TalentUP, RGPD fichaje, LOPDGDD control horario.
**Secundarias:** derechos ARCO-PLO, encargado tratamiento, cookies fichaje digital.
**Long-tail:** política privacidad control horario hostelería, RGPD registro jornada empleados.
**Intención:** informativa-legal.

---

## 3. Metadatos por página

### 3.1 Landing (`/`)

```html
<title>TalentUP Fichaje — Control horario NFC para hostelería</title>
<meta name="description" content="Control horario NFC, PIN y offline para restaurantes y tiendas. Nóminas automáticas, turnos y cumplimiento del RD-ley 8/2019 y RGPD. 14 días de prueba, sin permanencia.">
<meta name="keywords" content="fichaje digital, control horario, NFC, hostelería, restaurante, nóminas automáticas, RD-ley 8/2019, RGPD, control de presencia, gestión de turnos">
<link rel="canonical" href="https://talentup.es/">
<link rel="alternate" hreflang="es" href="https://talentup.es/">
<link rel="alternate" hreflang="x-default" href="https://talentup.es/">
<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:title" content="TalentUP Fichaje — Control horario NFC para hostelería">
<meta property="og:description" content="Fichaje NFC, PIN y offline. Nóminas automáticas y gestión de turnos. Cumple RGPD y RD-ley 8/2019.">
<meta property="og:image" content="https://talentup.es/og-image.png">
<meta property="og:url" content="https://talentup.es/">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="TalentUP Fichaje">
<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="TalentUP Fichaje — Control horario NFC para hostelería">
<meta name="twitter:description" content="Fichaje NFC, PIN y offline. Nóminas automáticas y gestión de turnos. Cumple RGPD y RD-ley 8/2019.">
<meta name="twitter:image" content="https://talentup.es/og-image.png">
```

### 3.2 Precios (`/pricing.html`)

```html
<title>Precios — TalentUP Fichaje | Control horario desde 29€/mes</title>
<meta name="description" content="Precios de TalentUP Fichaje. Tres planes para hostelería: Starter 29€/mes, Pro 99€/mes, Enterprise 499€/mes. Sin permanencia. Fichaje NFC, geolocalización, incidencias y exportación.">
<meta name="keywords" content="precios control horario, planes fichaje digital, tarifa software fichaje, fichaje hostelería precio, control horario SaaS coste">
<link rel="canonical" href="https://talentup.es/pricing.html">
<link rel="alternate" hreflang="es" href="https://talentup.es/pricing.html">
<link rel="alternate" hreflang="x-default" href="https://talentup.es/pricing.html">
<meta property="og:type" content="website">
<meta property="og:title" content="TalentUP Fichaje — Precios">
<meta property="og:description" content="Tres planes para hostelería. Starter 29€, Pro 99€, Enterprise 499€. Sin permanencia.">
<meta property="og:url" content="https://talentup.es/pricing.html">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="TalentUP Fichaje">
<meta property="og:image" content="https://talentup.es/og-image-pricing.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="TalentUP Fichaje — Precios">
<meta name="twitter:description" content="Tres planes para hostelería. Starter 29€, Pro 99€, Enterprise 499€.">
<meta name="twitter:image" content="https://talentup.es/og-image-pricing.png">
```

### 3.3 Contacto (`/contacto.html`)

```html
<title>Contacto — TalentUP Fichaje | Soporte y demos</title>
<meta name="description" content="Contacta con TalentUP Fichaje. Formulario de contacto, soporte técnico e información comercial para empresas de hostelería. Fichaje digital NFC.">
<meta name="keywords" content="contacto TalentUP, soporte fichaje digital, soporte técnico control horario, demo control horario hostelería">
<link rel="canonical" href="https://talentup.es/contacto.html">
<link rel="alternate" hreflang="es" href="https://talentup.es/contacto.html">
<link rel="alternate" hreflang="x-default" href="https://talentup.es/contacto.html">
<meta property="og:type" content="website">
<meta property="og:title" content="TalentUP Fichaje — Contacto">
<meta property="og:description" content="Soporte técnico e información comercial para empresas de hostelería.">
<meta property="og:url" content="https://talentup.es/contacto.html">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="TalentUP Fichaje">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="TalentUP Fichaje — Contacto">
<meta name="twitter:description" content="Soporte técnico e información comercial para empresas de hostelería.">
```

### 3.4 Términos (`/terminos.html`)

```html
<title>Términos de Servicio — TalentUP Fichaje</title>
<meta name="description" content="Términos de Servicio de TalentUP Fichaje. Plataforma SaaS B2B de fichaje digital para hostelería. Condiciones de uso, obligaciones, propiedad intelectual y ley aplicable.">
<meta name="keywords" content="términos servicio TalentUP, condiciones uso fichaje digital, contrato SaaS hostelería, propiedad intelectual software fichaje">
<link rel="canonical" href="https://talentup.es/terminos.html">
<link rel="alternate" hreflang="es" href="https://talentup.es/terminos.html">
<link rel="alternate" hreflang="x-default" href="https://talentup.es/terminos.html">
<!-- OG y Twitter: mismas que contacto, sustituyendo título/descripción/URL -->
```

### 3.5 Privacidad (`/privacidad.html`)

```html
<title>Política de Privacidad y Cookies — TalentUP Fichaje</title>
<meta name="description" content="Política de Privacidad y Cookies de TalentUP Fichaje. RGPD, LOPDGDD, derechos ARCO-PLO, encargado del tratamiento, conservación y medidas de seguridad.">
<meta name="keywords" content="política privacidad TalentUP, RGPD fichaje, LOPDGDD control horario, derechos ARCO-PLO, encargado tratamiento, cookies fichaje digital">
<link rel="canonical" href="https://talentup.es/privacidad.html">
<link rel="alternate" hreflang="es" href="https://talentup.es/privacidad.html">
<link rel="alternate" hreflang="x-default" href="https://talentup.es/privacidad.html">
<!-- OG y Twitter: mismas que contacto, sustituyendo título/descripción/URL -->
```

### 3.6 Dashboard, móvil y terminal (no indexables)

```html
<meta name="robots" content="noindex, nofollow">
```

Añadir esta etiqueta en `<head>` de `dashboard_new.html`, `mobile/index.html` y `terminal/index.html`. Refuerza el `Disallow` de `robots.txt` y evita indexación accidental.

---

## 4. Structured data (JSON-LD) por página

### 4.1 Landing (`/`) — SoftwareApplication + FAQPage + Organization + BreadcrumbList

**SoftwareApplication** (ya presente, mantener):
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "TalentUP Fichaje",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web, Android, iOS",
  "description": "Control horario NFC, PIN y offline para hostelería. Nóminas automáticas, gestión de turnos y cumplimiento del RGPD y del RD-ley 8/2019.",
  "url": "https://talentup.es/",
  "inLanguage": "es-ES",
  "offers": [
    {"@type": "Offer", "name": "Starter", "price": "29", "priceCurrency": "EUR", "description": "Hasta 15 empleados"},
    {"@type": "Offer", "name": "Pro", "price": "99", "priceCurrency": "EUR", "description": "Hasta 50 empleados, nóminas automáticas"},
    {"@type": "Offer", "name": "Enterprise", "price": "499", "priceCurrency": "EUR", "description": "Multi-empresa, empleados ilimitados"}
  ],
  "publisher": {"@type": "Organization", "name": "TalentUP", "url": "https://talentup.es"}
}
```

**FAQPage** (ya presente, 6 preguntas, mantener). Cubre RGPD, hardware, offline, integración nóminas, cancelación y soporte.

**Organization** (añadir):
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "TalentUP",
  "url": "https://talentup.es",
  "logo": "https://talentup.es/icon-512.svg",
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer support",
    "email": "hola@talentup.es",
    "availableLanguage": ["Spanish"]
  }
}
```

**BreadcrumbList** (añadir en landing y todas las páginas internas):
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://talentup.es/"},
    {"@type": "ListItem", "position": 2, "name": "Precios", "item": "https://talentup.es/pricing.html"}
  ]
}
```

> **Nota:** No reincorporar `aggregateRating` (4.8/120) hasta tener reseñas verificables. Google penaliza rich snippets fabricados.

### 4.2 Precios (`/pricing.html`) — Product + Offer + FAQPage

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "TalentUP Fichaje — Control horario hostelería",
  "description": "Software de fichaje digital NFC, PIN y offline para hostelería.",
  "brand": {"@type": "Brand", "name": "TalentUP"},
  "offers": [
    {"@type": "Offer", "name": "Starter", "price": "29", "priceCurrency": "EUR", "priceValidUntil": "2026-12-31", "url": "https://talentup.es/pricing.html"},
    {"@type": "Offer", "name": "Pro", "price": "99", "priceCurrency": "EUR", "priceValidUntil": "2026-12-31", "url": "https://talentup.es/pricing.html"},
    {"@type": "Offer", "name": "Enterprise", "price": "499", "priceCurrency": "EUR", "priceValidUntil": "2026-12-31", "url": "https://talentup.es/pricing.html"}
  ]
}
```

**FAQPage** con las 7 preguntas de la página: permanencia, cambio de plan, qué cuenta como empleado, hardware NFC, plan Starter gratuito, descuento anual y seguridad de datos.

### 4.3 Contacto (`/contacto.html`) — ContactPage + Organization

```json
{
  "@context": "https://schema.org",
  "@type": "ContactPage",
  "name": "Contacto — TalentUP Fichaje",
  "url": "https://talentup.es/contacto.html",
  "inLanguage": "es-ES",
  "mainEntity": {
    "@type": "Organization",
    "name": "TalentUP",
    "url": "https://talentup.es",
    "email": "hola@talentup.es",
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer support",
      "availableLanguage": ["Spanish"]
    }
  }
}
```

### 4.4 Términos (`/terminos.html`) — WebPage + BreadcrumbList

```json
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Términos de Servicio — TalentUP Fichaje",
  "url": "https://talentup.es/terminos.html",
  "inLanguage": "es-ES",
  "isPartOf": {"@type": "WebSite", "name": "TalentUP Fichaje", "url": "https://talentup.es"}
}
```

### 4.5 Privacidad (`/privacidad.html`) — WebPage + BreadcrumbList

Mismo patrón que Términos, sustituyendo `name` y `url`. Añadir referencia a normativa: `"about": {"@type": "Thing", "name": "RGPD"}`.

### 4.6 WebSite (global, en landing)

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "TalentUP Fichaje",
  "url": "https://talentup.es",
  "inLanguage": "es-ES",
  "publisher": {"@type": "Organization", "name": "TalentUP"}
}
```

---

## 5. Sitemap.xml

Archivo: `public/sitemap.xml` (servido en `https://talentup.es/sitemap.xml`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">

  <!-- Landing principal -->
  <url>
    <loc>https://talentup.es/</loc>
    <lastmod>2026-08-09</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>

  <!-- Precios -->
  <url>
    <loc>https://talentup.es/pricing.html</loc>
    <lastmod>2026-08-09</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>

  <!-- Contacto -->
  <url>
    <loc>https://talentup.es/contacto.html</loc>
    <lastmod>2026-08-09</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>

  <!-- Términos -->
  <url>
    <loc>https://talentup.es/terminos.html</loc>
    <lastmod>2026-08-09</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>

  <!-- Privacidad -->
  <url>
    <loc>https://talentup.es/privacidad.html</loc>
    <lastmod>2026-08-09</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>

</urlset>
```

**Excluidos del sitemap** (no indexables): `dashboard_new.html`, `index.html` (app), `offline.html`, `/mobile/`, `/terminal/`, `/api/`.

> Eliminar la entrada `PRIVACY.md` del sitemap actual (es un documento Markdown de repo, no una página pública). El sitemap debe listar solo las 5 URLs indexables.

---

## 6. Robots.txt

Archivo: `public/robots.txt` (servido en `https://talentup.es/robots.txt`).

```txt
# TalentUP Fichaje — robots.txt
# Fichaje digital NFC, PIN y offline para hostelería
# https://talentup.es

User-agent: *
Allow: /

# Páginas privadas / dashboard no indexables
Disallow: /dashboard
Disallow: /dashboard_new.html
Disallow: /index.html
Disallow: /mobile/
Disallow: /terminal/
Disallow: /offline.html
Disallow: /api/

# No rastrear parámetros de seguimiento ni sesiones
Disallow: /*?session
Disallow: /*?token
Disallow: /*?utm_

# Bots de IA generativa — permitidos para visibilidad en respuestas
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Bingbot
Allow: /

# Sitemap
Sitemap: https://talentup.es/sitemap.xml
```

**Cambios respecto al actual:** añadir `Disallow: /mobile/` y `Disallow: /terminal/` (las PWAs no deben indexarse).

---

## 7. Optimización para IA generativa (GEO / AEO)

Los bots de IA (GPTBot, PerplexityBot, ClaudeBot, Google-Extended) ya están permitidos en `robots.txt`. Para mejorar la visibilidad en respuestas de ChatGPT, Perplexity y Gemini:

1. **Preguntas FAQ con respuesta directa** — ya cubierto en landing (6 Q&A) y pricing (7 Q&A). Mantener formato pregunta-respuesta conciso.
2. **Datos estructurados** — los `FAQPage` y `SoftwareApplication` son clave para que los LLM extraigan información precisa.
3. **Lenguaje natural y específico** — usar "control horario para hostelería", no "solución RRHH". Los LLM citan fuentes concretas.
4. **Datos verificables** — precios exactos (29€/99€/499€), normativa citada (RGPD, RD-ley 8/2019), hardware opcional (kit NFC 49€).
5. **Contenido en `es-ES`** — el mercado objetivo es España; no traducir a otros idiomas (perjudica densidad de keyword).
6. **Estructura semántica H1-H3** — cada página con un único H1, H2 por sección, H3 para subsecciones. Ya implementado en landing y dashboard.

---

## 8. Checklist de implementación

- [ ] Actualizar `sitemap.xml`: 5 URLs indexables, eliminar `PRIVACY.md`.
- [ ] Actualizar `robots.txt`: añadir `Disallow: /mobile/` y `Disallow: /terminal/`.
- [ ] Añadir `<meta name="robots" content="noindex, nofollow">` en `dashboard_new.html`, `mobile/index.html`, `terminal/index.html`.
- [ ] Añadir `meta keywords` en pricing, contacto, términos y privacidad (actualmente ausentes).
- [ ] Añadir `Organization` JSON-LD en landing.
- [ ] Añadir `Product` + `Offer` JSON-LD en pricing.
- [ ] Añadir `ContactPage` JSON-LD en contacto.
- [ ] Añadir `WebPage` JSON-LD en términos y privacidad.
- [ ] Añadir `BreadcrumbList` en pricing, contacto, términos y privacidad.
- [ ] Añadir `og:image` dedicada para pricing (`og-image-pricing.png`).
- [ ] Añadir `WebSite` JSON-LD global en landing.
- [ ] Generar `og-image.png` (1200×630) para landing.
- [ ] Enviar sitemap en Google Search Console y Bing Webmaster Tools.
- [ ] No reincorporar `aggregateRating` hasta tener reseñas reales verificables.

---

## 9. Métricas y seguimiento

- **Google Search Console** — monitorizar impresiones de "control horario hostelería", CTR y posición media.
- **Bing Webmaster Tools** — idem para Bing.
- **Google Analytics 4** — seguimiento de tráfico orgánico y conversión por página.
- **KPIs SEO:** posicionamiento top-10 para "control horario hostelería", "fichaje digital", "fichaje NFC"; tráfico orgánico mensual; tasa de conversión orgánico→trial.

---

*Documento generado el 2026-08-09. Revisar trimestralmente y tras cada cambio de página.*