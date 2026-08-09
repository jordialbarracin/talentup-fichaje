# Documento de Performance — TalentUP Frontend

> Guía técnica de optimización de rendimiento para el frontend de TalentUP (dashboard, landing, pricing, contacto, términos, privacidad, terminal y vista móvil). Objetivo: **Lighthouse ≥ 90** en Performance, Accessibility, Best Practices y SEO.

---

## 1. Objetivos de Rendimiento (Lighthouse Score Target)

### 1.1 Core Web Vitals — Métricas Objetivo

| Métrica | Target | Estado "Good" | Estado "Poor" |
|---------|--------|---------------|---------------|
| **LCP** (Largest Contentful Paint) | < 2.5 s | < 2.5 s | > 4.0 s |
| **CLS** (Cumulative Layout Shift) | < 0.1 | < 0.1 | > 0.25 |
| **INP** (Interaction to Next Paint) | < 200 ms | < 200 ms | > 500 ms |
| **FCP** (First Contentful Paint) | < 1.8 s | < 1.8 s | > 3.0 s |
| **TTFB** (Time to First Byte) | < 800 ms | < 800 ms | > 1.8 s |

### 1.2 Scores Lighthouse Objetivo

- **Performance**: ≥ 90 (óptimo 95+)
- **Accessibility**: ≥ 95 (óptimo 100)
- **Best Practices**: ≥ 95
- **SEO**: ≥ 95

### 1.3 Presupuesto de Performance (Performance Budget)

```
JavaScript total (initial load):   ≤ 170 KB gzipped
CSS total (initial load):          ≤ 30 KB gzipped
Imágenes (landing LCP):            ≤ 100 KB
Fuentes web:                       ≤ 50 KB
Requests iniciales (landing):      ≤ 20
Requests iniciales (dashboard):    ≤ 25
```

Estos presupuestos se validan en CI con `lighthouse-ci` o `bundlewatch`. Si un PR los excede, el build falla.

---

## 2. Lazy Loading y Code Splitting

### 2.1 Code Splitting por Rutas

TalentUP tiene 8 vistas principales. Cargarlas todas en un único bundle penaliza el Time to Interactive de la landing. Se aplica **route-based code splitting** con `React.lazy` + `Suspense` (o `defineAsyncComponent` en Vue):

```jsx
const Dashboard   = React.lazy(() => import('./pages/Dashboard'));
const Pricing     = React.lazy(() => import('./pages/Pricing'));
const Contacto    = React.lazy(() => import('./pages/Contacto'));
const Terminos    = React.lazy(() => import('./pages/Terminos'));
const Privacidad  = React.lazy(() => import('./pages/Privacidad'));
const Terminal    = React.lazy(() => import('./pages/Terminal'));

<Route path="/dashboard" element={
  <Suspense fallback={<PageSkeleton />}><Dashboard /></Suspense>
} />
```

- La **landing** es la única ruta eager (bundle inicial), porque es el LCP crítico.
- Las rutas legales (términos, privacidad) se cargan bajo demanda — raramente visitadas.
- El **dashboard** se pre-carga (`prefetch`) tras el primer paint de la landing, dado que es el siguiente flujo del usuario autenticado.

### 2.2 Prefetch Inteligente

```jsx
import { useEffect } from 'react';
// Al hacer hover en un enlace de navegación, prefetch del chunk
const onHoverPrefetch = (route) => import(`./pages/${route}`);
```

Patrones aplicados:
- **Prefetch on idle**: `webpackPrefetch: true` para rutas de alta probabilidad.
- **Prefetch on hover**: para enlaces de navegación principal.
- **Prefetch on visible**: con `IntersectionObserver` para contenido below-the-fold.

### 2.3 Lazy Loading de Componentes Pesados

- **Gráficos del dashboard** (Recharts/Chart.js): `React.lazy`, solo se cargan cuando el dashboard se monta.
- **Editor de terminal**: se carga exclusivamente en la ruta `/terminal`.
- **Mapas** (si los hay): `React.lazy` con `IntersectionObserver`.
- **Modales y drawers**: cargados al primer `click`, no en el bundle inicial.

### 2.4 Vendor Splitting

```js
// vite.config.js / webpack.config.js
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'react-vendor': ['react', 'react-dom', 'react-router-dom'],
        'charts': ['recharts', 'd3-scale'],
        'forms': ['react-hook-form', 'zod'],
      }
    }
  }
}
```

Esto separa librerías estables (cacheo a largo plazo) del código de aplicación (cambia frecuentemente).

---

## 3. Optimización de Imágenes

### 3.1 Formatos Modernos

- **WebP/AVIF** como formato primario con fallback JPEG/PNG.
- **`<picture>`** con `srcset` para servir el formato que el navegador soporte:

```html
<picture>
  <source srcset="/img/hero.avif" type="image/avif">
  <source srcset="/img/hero.webp" type="image/webp">
  <img src="/img/hero.jpg" alt="TalentUP dashboard" loading="lazy" width="1200" height="630">
</picture>
```

### 3.2 Imagen Responsiva (srcset)

```html
<img srcset="/img/hero-480.webp 480w,
             /img/hero-800.webp 800w,
             /img/hero-1200.webp 1200w"
     sizes="(max-width: 600px) 480px, 800px"
     src="/img/hero-800.webp" alt="Hero">
```

El navegador descarga solo la resolución adecuada al viewport — clave en móvil.

### 3.3 Lazy Loading Nativo

- Todas las imágenes below-the-fold: `loading="lazy"`.
- La imagen LCP (hero de landing): `loading="eager"` + `fetchpriority="high"` + `preload`.
- **Preload del LCP** en el `<head>`:

```html
<link rel="preload" as="image" href="/img/hero.webp"
      imagesrcset="/img/hero-480.webp 480w, /img/hero-800.webp 800w"
      imagesizes="100vw" fetchpriority="high">
```

### 3.4 Dimensiones Explícitas

Toda imagen debe llevar `width` y `height` para **evitar CLS**. El navegador reserva el espacio antes de la descarga.

### 3.5 Pipeline de Build

- Plugin `vite-imagetools` o `vite-plugin-imagemin` en build.
- Compresión: `mozjpeg` (calidad 75), `pngquant` (calidad 65-80), `webp` (calidad 80).
- Generación automática de versiones AVIF + WebP para cada imagen.
- Imágenes de iconos → **SVG inline** (cero requests adicionales).

### 3.6 Imágenes de Usuario (avatars, logos subidos)

- Re-dimensionar servidor-side al tamaño máximo requerido (ej. 256×256 para avatares).
- Servir vía CDN con transformación on-the-fly (Cloudflare Images, Imgix).

---

## 4. Caché

### 4.1 Caché HTTP — Niveles

**Assets con hash (inmutables)** — JS/CSS/imagenes con fingerprint `[name].[hash].js`:
```
Cache-Control: public, max-age=31536000, immutable
```
Estos archivos nunca cambian — el navegador los cachea 1 año y nunca los re-valida.

**HTML (sin hash)**:
```
Cache-Control: no-cache
```
Siempre re-valida (ETag/Last-Modified) para servir la última versión.

**API responses**:
```
Cache-Control: private, max-age=0, must-revalidate
```

### 4.2 Caché del Navegador (Service Worker)

Para la vista móvil y el dashboard offline-capable:

```js
// workbox / vite-plugin-pwa
new VitePWA({
  workbox: {
    runtimeCaching: [
      { urlPattern: /\.(js|css|woff2)$/, handler: 'CacheFirst',
        options: { cacheName: 'static', expiration: { maxEntries: 100 } } },
      { urlPattern: /\/api\/.*$/, handler: 'NetworkFirst',
        options: { cacheName: 'api', networkTimeoutSeconds: 3 } },
      { urlPattern: /\.(webp|avif|png)$/, handler: 'CacheFirst',
        options: { cacheName: 'images' } },
    ]
  }
})
```

- Estrategia **CacheFirst** para assets inmutables.
- Estrategia **NetworkFirst** (con timeout) para datos de la API del dashboard.
- Estrategia **StaleWhileRevalidate** para fuentes y logos.

### 4.3 Caché de Datos en Cliente (React Query / SWR)

```js
const { data } = useQuery(['fichajes'], fetchFichajes, {
  staleTime: 60_000,        // 1 min antes de re-fetch
  cacheTime: 5 * 60_000,    // 5 min en cache
});
```

Evita refetch innecesario al navegar entre vistas del dashboard.

---

## 5. CDN (Content Delivery Network)

### 5.1 Arquitectura CDN

Todo el frontend estático se sirve desde un CDN con **puntos de presencia (PoPs)** globales:

- **Cloudflare Pages / Vercel Edge / Netlify Edge** para hosting.
- Los assets se replican en ~250 PoPs, reduciendo latencia RTT.
- **Cacheo en el edge**: HTML y assets cacheados en el PoP más cercano al usuario.

### 5.2 Configuración CDN

```
# Origen: servidor de build (GitHub Actions → deploy estático)
# Reglas de cache en el edge:
/assets/*   → 1 año, immutable, cache everywhere
/*.html     → 30 s, edge TTL, bypass on revalidation
/api/*      → no cache en CDN, pass-through al backend
```

### 5.3 Edge Functions / SSR en el Edge

Para contenido dinámico de la landing (precios actualizados, test A/B):
- **Edge SSR** con Vercel/Cloudflare Workers.
- TTFB < 100 ms en cualquier región.
- Render del HTML inicial en el edge, hidratación en el cliente.

### 5.4 Compresión Brotli/Gzip

- **Brotli level 11** para HTML, CSS, JS (compresión 15-20% mejor que gzip).
- **Gzip level 6** como fallback.
- Configurado en el CDN automáticamente; en origen solo si no hay CDN.

### 5.5 HTTP/2 y HTTP/3

- **HTTP/2** multiplexado: múltiples requests sobre una conexión TCP.
- **HTTP/3 (QUIC)**: reduce el coste del handshake TLS, 0-RTT para visitantes recurrentes.
- Elimina la necesidad de "domain sharding" — un solo dominio basta.

---

## 6. Optimizaciones Adicionales

### 6.1 Fuentes Web

```html
<link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
```

- Usar **`font-display: swap`** para mostrar texto inmediatamente con fuente del sistema.
- Self-host de fuentes (evita requests a Google Fonts, reduce TTFB).
- **Subset de fuentes**: solo caracteres latinos (reduce 80% del peso).
- Variable fonts: un solo archivo cubre todos los pesos.

### 6.2 CSS Crítico (Critical CSS)

- Inline del CSS crítico (above-the-fold) en el `<head>`: ~10-14 KB.
- El resto del CSS se carga asíncrono:

```html
<link rel="preload" href="/assets/app.[hash].css" as="style" onload="this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="/assets/app.[hash].css"></noscript>
```

### 6.3 JavaScript Crítico

- Minimizar JS en el bundle inicial — solo el necesario para la landing.
- Diferir JS no esencial: `defer` o `async`.
- Eliminar JS muerto con tree-shaking (`sideEffects: false` en `package.json`).
- Analizar el bundle con `rollup-plugin-visualizer` para detectar dependencias pesadas.

### 6.4 Renderizado

- **Preconnect** a orígenes de terceros:

```html
<link rel="preconnect" href="https://api.talentup.com">
<link rel="dns-prefetch" href="https://cdn.talentup.com">
```

- **`content-visibility: auto`** para secciones below-the-fold del dashboard (skip render hasta que son visibles):

```css
.dashboard-row { content-visibility: auto; contain-intrinsic-size: 0 80px; }
```

### 6.5 Virtualización de Listas Largas

El dashboard puede mostrar miles de fichajes. Se virtualiza con `react-window` o `@tanstack/react-virtual`:

```jsx
import { FixedSizeList as List } from 'react-window';
<List height={600} itemCount={10000} itemSize={60} width="100%">
  {Row}
</List>
```

Solo se renderizan las filas visibles (~15), no las 10.000.

### 6.6 Vista Móvil

- **Viewport meta** correcto: `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- Media queries con `min-width` (mobile-first).
- Evitar `position: fixed` excesivo (causa repaints costosos en scroll).
- `touch-action: manipulation` para botones (elimina el delay de 300ms).
- Imágenes en móvil: servir variantes de menor resolución (srcset).

---

## 7. Monitoreo y CI

### 7.1 Lighthouse CI

```yaml
# .github/workflows/lighthouse.yml
- uses: treosh/lighthouse-ci-action@v11
  with:
    urls: |
      https://talentup.com
      https://talentup.com/dashboard
      https://talentup.com/pricing
    budgetPath: ./lighthouse-budget.json
    uploadArtifacts: true
```

`lighthouse-budget.json`:
```json
{
  "resourceCounts": [{ "resourceType": "script", "budget": 10 }],
  "resourceSizes": [
    { "resourceType": "script", "budget": 170 },
    { "resourceType": "stylesheet", "budget": 30 }
  ]
}
```

### 7.2 RUM (Real User Monitoring)

- **Web Vitals JS library** envía LCP/CLS/INP reales a un dashboard (Datadog RUM, Vercel Analytics, SpeedCurve).
- Alertas si el p75 de LCP supera 2.5 s durante 24 h.
- Segmentación por dispositivo, red y país para detectar regresiones regionales.

### 7.3 Tests de Performance

- **Lighthouse CI** en cada PR (gate: Performance ≥ 90).
- **Bundle size check**: si el bundle crece > 5%, el CI falla.
- **Lighthouse CI assertions**:

```json
{
  "assertions": {
    "categories:performance": ["warn", { "minScore": 0.9 }],
    "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
    "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }]
  }
}
```

---

## 8. Checklist de Optimización

- [ ] Code splitting por ruta aplicado
- [ ] Lazy loading de componentes pesados (gráficos, terminal, modales)
- [ ] Vendor chunks separados (react, charts, forms)
- [ ] Imágenes en WebP/AVIF con `<picture>` y `srcset`
- [ ] `loading="lazy"` en imágenes below-the-fold
- [ ] Preload de imagen LCP con `fetchpriority="high"`
- [ ] `width`/`height` en todas las imágenes (evitar CLS)
- [ ] `Cache-Control: immutable` para assets con hash
- [ ] Service Worker con estrategias de cache (CacheFirst/NetworkFirst)
- [ ] React Query / SWR con `staleTime` para datos del dashboard
- [ ] CDN configurado con Brotli + HTTP/3
- [ ] Fuentes self-hosted con `font-display: swap` y subsetting
- [ ] Critical CSS inlineado en el `<head>`
- [ ] `preconnect` a orígenes de terceros
- [ ] Virtualización de listas largas en el dashboard
- [ ] `content-visibility: auto` en secciones below-the-fold
- [ ] Lighthouse CI con presupuesto de performance en CI
- [ ] RUM con Web Vitals en producción
- [ ] Lighthouse ≥ 90 en Performance verificado en CI

---

## 9. Resumen Ejecutivo

La estrategia de performance de TalentUP se estructura en **cinco pilares**:

1. **Code splitting** — cargar solo lo necesario por ruta, con prefetch inteligente.
2. **Imagen optimizada** — formatos modernos, responsive, lazy y preload del LCP.
3. **Caché multicapa** — HTTP inmutable, Service Worker, caché de datos en cliente.
4. **CDN global** — edge caching, Brotli, HTTP/3, edge SSR para contenido dinámico.
5. **Monitoreo continuo** — Lighthouse CI + RUM para detectar regresiones.

El objetivo cuantitativo es **Lighthouse Performance ≥ 90** con Core Web Vitals en verde: LCP < 2.5 s, CLS < 0.1, INP < 200 ms. Estos umbrales no son aspiracionales — son **puertas de calidad en CI** que bloquean cualquier merge que los degrade.

---

*Documento técnico de performance — TalentUP Frontend. Última revisión: agosto 2026.*