# TalentUP Fichaje — Guía de Estilo

> **Fuente de verdad:** `design_system.css` (derivado de `talentup_design_vision.md`, 8 agosto 2026).
> **Superficies:** Landing · Dashboard · PWA empleado · Terminal kiosco.
> **Convención de tokens:** todo valor vivo como variable CSS (`--token`). No se hardcodean colores, radios ni espacios en componentes.

---

## 1. Principios de diseño

El sistema se sostiene sobre cuatro reglas que el CSS hace cumplir por construcción:

1. **El naranja es acento, no protagonista.** Jamás se usa como fondo de superficie grande. Aparece en botones primarios, enlaces activos, foco y detalles. Tintes al 6–12 % para fondos contextuales.
2. **Claridad bajo presión.** Los targets táctiles son ≥ 44 px en app y ≥ 60 px en kiosco. La jerarquía tipográfica se respeta sin caer en escalas decorativas.
3. **Confianza silenciosa.** Sin gradientes decorativos, sin sombras dramáticas. La elevación se sugiere, no se dramatiza. Una sola familia de sombras, nada más oscuro que 0.08 de alpha.
4. **Un solo sistema, cuatro superficies.** Todo valor vive aquí como token. Si un color o radio no está definido, no existe.

**Decisión de color:** los valores hex se mantienen como fuente de verdad (no se convierten a OKLCH) porque el objetivo declarado es coincidir con los colores de sistema de Apple (Apple HIG). Los tintes se expresan en `rgba()` sobre esos mismos valores base.

**Decisión de modo oscuro:** el sistema no tiene modo oscuro por decisión de producto. Si el navegador fuerza uno, se mantiene la superficie clara en vez de degradar a un oscuro no diseñado.

---

## 2. Paleta de colores

### 2.1 Neutrales

| Token | HEX / Valor | Uso |
|---|---|---|
| `--text-primary` | `#1d1d1f` | Texto principal, títulos |
| `--text-secondary` | `#6e6e73` | Texto secundario, labels, muted |
| `--text-tertiary` | `rgba(0,0,0,0.32)` | Metadatos, placeholders |
| `--text-quaternary` | `rgba(0,0,0,0.15)` | Marcas de agua, versión |
| `--text-on-brand` | `#ffffff` | Texto sobre superficies de marca |
| `--bg-app` | `#f5f5f7` | Fondo de aplicación |
| `--bg-surface` | `#ffffff` | Tarjetas, modales, inputs enfocados |
| `--bg-sunken` | `#fafafa` | Bandas alternas de landing |
| `--bg-hover` | `rgba(0,0,0,0.04)` | Hover de superficies neutras |
| `--bg-pressed` | `rgba(0,0,0,0.07)` | Pressed de superficies neutras |
| `--bg-scrim` | `rgba(0,0,0,0.25)` | Overlay de modal |
| `--border` | `rgba(0,0,0,0.06)` | Bordes estándar |
| `--border-strong` | `rgba(0,0,0,0.12)` | Bordes reforzados |
| `--border-hairline` | `rgba(0,0,0,0.04)` | Separadores mínimos |

### 2.2 Acento de marca (naranja)

| Token | HEX | Uso |
|---|---|---|
| `--brand` | `#FF6B35` | Acento principal, botón primario, enlaces |
| `--brand-hover` | `#E55A2B` | Hover de primario |
| `--brand-pressed` | `#CC4E22` | Pressed de primario |
| `--brand-tint-06` | `rgba(255,107,53,0.06)` | Fondo contextual sutil |
| `--brand-tint-08` | `rgba(255,107,53,0.08)` | Nav activa |
| `--brand-tint-12` | `rgba(255,107,53,0.12)` | Selección, badge "late" |
| `--brand-tint-35` | `rgba(255,107,53,0.35)` | Ring de foco en inputs |

### 2.3 Semánticos

| Token | HEX | Uso |
|---|---|---|
| `--success` | `#34C759` | Éxito (fondo/superficie de marca) |
| `--success-strong` | `#248A3D` | Éxito AA sobre blanco (texto) |
| `--success-tint` | `rgba(52,199,89,0.12)` | Badge OK, presencia en vivo |
| `--danger` | `#FF3B30` | Error destructivo |
| `--danger-hover` | `#E02E24` | Hover de danger |
| `--danger-tint` | `rgba(255,59,48,0.12)` | Badge incidente/rechazado, error de input |
| `--warning` | `#FF9500` | Advertencia (superficie de marca) |
| `--warning-strong` | `#B25E00` | Advertencia AA sobre blanco (texto) |
| `--warning-tint` | `rgba(255,149,0,0.12)` | Badge pending, banner offline |
| `--info` | `#007AFF` | Uso puntual — **no es el default de nada** |
| `--info-tint` | `rgba(0,122,255,0.10)` | Badge "on leave" |

**Regla de contraste AA:** para texto sobre blanco se usan las variantes `-strong` (`success-strong`, `warning-strong`), no las versiones base de `#34C759` / `#FF9500`.

---

## 3. Tipografía

### 3.1 Familias

- **Sans (default):** `-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
- **Mono:** `ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace` — reservada para micro (versión, timestamps técnicos).

### 3.2 Escala de APP (dashboard, PWA, kiosco)

| Token | Tamaño | Uso |
|---|---|---|
| `--text-display` | 34 px | Reloj del kiosco, cifra dominante |
| `--text-h1` | 22 px | Título de página |
| `--text-h2` | 18 px | Título de sección / tarjeta |
| `--text-body` | 15 px | Párrafo, listas (default del body) |
| `--text-body-sm` | 14 px | Metadatos, descripciones |
| `--text-caption` | 13 px | Labels de tabla, badges |
| `--text-micro` | 11 px | Versión, timestamps técnicos (mono) |

### 3.3 Escala de MARKETING (solo landing)

Extensión deliberada y **única desviación** de la escala de app. Compiten por atención en 3 segundos en monitores grandes. Viven separadas para que nadie las use dentro del dashboard.

| Token | Tamaño | Uso |
|---|---|---|
| `--text-hero` | `clamp(2.25rem, 1.35rem + 3.6vw, 3.5rem)` (36 → 56 px) | Titular principal |
| `--text-section` | `clamp(1.75rem, 1.25rem + 2vw, 2.5rem)` (28 → 40 px) | Cabecera de sección |
| `--text-lead` | `clamp(1.0625rem, 0.98rem + 0.35vw, 1.25rem)` (17 → 20 px) | Párrafo introductorio |

### 3.4 Tracking (letter-spacing)

| Token | Valor | Uso |
|---|---|---|
| `--tracking-tight` | `-0.03em` | Display / hero |
| `--tracking-snug` | `-0.028em` | H1 |
| `--tracking-normal` | `-0.022em` | H2, body — default del sistema |
| `--tracking-caption` | `-0.01em` | Caption |
| `--tracking-wide` | `0.03em` | Micro, mayúsculas |
| `--tracking-label` | `0.06em` | Labels en mayúsculas |

### 3.5 Interlineado

| Token | Valor | Uso |
|---|---|---|
| `--leading-tight` | 1.1 | Display / hero |
| `--leading-snug` | 1.25 | H1, H2 |
| `--leading-normal` | 1.5 | Body (default) |
| `--leading-relaxed` | 1.6 | Párrafos largos |

### 3.6 Clases utilitarias de texto

`.t-display`, `.t-h1`, `.t-h2`, `.t-body`, `.t-body-sm`, `.t-caption`, `.t-micro` aplican tamaño + peso + tracking + leading en bloque.

Colores semánticos de texto: `.t-muted` (secondary), `.t-faint` (tertiary), `.t-brand`, `.t-danger`, `.t-success` (usa `-strong`), `.t-warning` (usa `-strong`).

`.t-label` — label en mayúsculas: `--text-micro`, peso 600, `text-transform: uppercase`, tracking `0.06em`, color secondary. Para cabeceras de tabla y labels de formulario.

**Tabular nums:** `.tabular`, `.stat-card-value`, `.clock-live` aplican `font-variant-numeric: tabular-nums`. Obligatorio en cifras que se actualizan en vivo (un contador de horas hace saltar el layout cada segundo sin esto, porque el "1" es más estrecho que el "0").

`.measure` — `max-width: 68ch` para párrafos legibles.

Los títulos largos no rompen el layout en móvil: `h1, h2, h3, .t-display, .t-h1` llevan `overflow-wrap: anywhere; min-width: 0`.

---

## 4. Espaciado

Escala de **4 pt**. Ningún valor fuera de esta escala.

| Token | px | Token | px |
|---|---|---|---|
| `--space-1` | 4 | `--space-8` | 32 |
| `--space-2` | 8 | `--space-10` | 40 |
| `--space-3` | 12 | `--space-12` | 48 |
| `--space-4` | 16 | `--space-16` | 64 |
| `--space-5` | 20 | `--space-20` | 80 |
| `--space-6` | 24 | `--space-25` | 100 |
| `--space-7` | 28 | | |

Utilidades: `.gap-1` … `.gap-6`, `.mt-2/4/6`, `.mb-2/4/6`.

---

## 5. Radios

| Token | px | Uso |
|---|---|---|
| `--radius-xs` | 4 | Badge cuadrado, skeleton |
| `--radius-sm` | 6 | Item de nav, modal-close |
| `--radius-md` | 8 | Input, icono contenedor, toast |
| `--radius-lg` | 10 | Tarjeta de app |
| `--radius-xl` | 12 | Tarjeta de landing, modal |
| `--radius-2xl` | 16 | Superficie destacada |
| `--radius-pill` | 980px | Botón, pastilla de estado, switch, segmented |

---

## 6. Sombras

Una sola familia. Nada más oscuro que 0.08 de alpha. El sistema es **plano por decisión**: la elevación se sugiere, no se dramatiza.

| Token | Valor | Uso |
|---|---|---|
| `--shadow-hairline` | `0 1px 2px rgba(0,0,0,0.04)` | Reposo de tarjeta, knob de switch |
| `--shadow-card` | `0 1px 2px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.06)` | Tarjeta elevada |
| `--shadow-raised` | `0 2px 8px rgba(0,0,0,0.06)` | Hover de tarjeta |
| `--shadow-float` | `0 4px 12px rgba(0,0,0,0.06), 0 12px 32px rgba(0,0,0,0.06)` | Dropdown, popover |
| `--shadow-modal` | `0 4px 16px rgba(0,0,0,0.08)` | Modal, toast, skip-link |

Sin sombras de color. Sin `box-shadow` decorativa de marca.

---

## 7. Movimiento

| Token | Duración | Uso |
|---|---|---|
| `--dur-instant` | 100ms | Micro-ajustes |
| `--dur-fast` | 150ms | Transform de botón (active) |
| `--dur-base` | 200ms | Estándar: hover, focus, modal |
| `--dur-slow` | 300ms | Toast slide in/out |

Curvas:
- `--ease-out`: `cubic-bezier(0.16, 1, 0.3, 1)` — default (entradas)
- `--ease-in`: `cubic-bezier(0.4, 0, 1, 1)` — salidas
- `--ease-in-out`: `cubic-bezier(0.4, 0, 0.2, 1)` — transiciones bidireccionales

**Keyframes propios:** `tu-fade-in`, `tu-rise` (translateY 8px), `tu-spin`, `tu-shimmer` (skeleton), `tu-pulse` (1.6s, dot de syncing), `tu-slide-in` / `tu-slide-out` (translateX 16px).

---

## 8. Layout

| Token | Valor | Uso |
|---|---|---|
| `--sidebar-w` | 224px | Sidebar expandido |
| `--sidebar-rail-w` | 60px | Colapso icono-only en tablet |
| `--navbar-h` | 56px | Altura de navbar |
| `--container` | 1100px | Ancho máximo de contenido |
| `--measure` | 68ch | Ancho máximo de párrafo legible |
| `--touch-min` | 44px | Target táctil mínimo (Apple HIG). Kiosco → 60px |

### Z-index

Escala estricta, sin solapamientos:

| Token | Valor | Capa |
|---|---|---|
| `--z-base` | 1 | Contenido base |
| `--z-sticky` | 30 | Sticky headers |
| `--z-sidebar` | 40 | Sidebar |
| `--z-navbar` | 50 | Navbar |
| `--z-modal` | 100 | Modal overlay |
| `--z-toast` | 200 | Toast |

El skip-link usa `calc(--z-toast + 1)` para quedar siempre encima.

---

## 9. Componentes

### 9.1 Marca — logo y wordmark

Dirección A del documento: reloj + arcos NFC. El glifo se dibuja con `currentColor` para heredar el contexto (naranja sobre blanco, blanco sobre naranja) sin duplicar assets.

- `.tu-lockup` — contenedor inline-flex, gap `--space-2`.
- `.tu-mark` — glifo SVG, `color: --brand`, `flex-shrink: 0`.
- `.tu-wordmark` — `--text-h2`, peso 600. El `<em>` del "UP" se tiñe de naranja.
- Variantes inversas: `.tu-mark--inverse`, `.tu-lockup--inverse` (texto blanco).

**Regla de uso:** por debajo de 24 px el arco exterior se pierde y ensucia el glifo. A tamaño favicon se suelta, no se comprime (`.tu-mark--sm .tu-mark-arc-outer { display: none }`).

### 9.2 Botones

Cuatro variantes, ocho estados cada una. **Una sola acción primaria por pantalla** — la secundaria nunca compite visualmente.

Base `.btn`: inline-flex, `min-height: 36px`, padding `--space-2 --space-4`, `radius-pill`, `--text-caption`, peso 500, `white-space: nowrap`, border 1px transparent. Transición de background, border-color, color (base) y transform (fast). `:active` → `scale(0.97)`.

| Variante | Reposo | Hover |
|---|---|---|
| `.btn-primary` | bg `--brand`, texto `--text-on-brand` | bg `--brand-hover` |
| `.btn-secondary` | transparente, texto `--brand`, border `--brand-tint-35` | bg `--brand-tint-06`, border `--brand` |
| `.btn-ghost` | transparente, texto `--text-secondary` | bg `--bg-hover`, texto `--text-primary` |
| `.btn-danger` | bg `--danger`, texto blanco | bg `--danger-hover` |

**Tamaños:**
- `.btn-sm` — `min-height: 30px`, `--text-micro`
- `.btn-lg` — `min-height: 44px` (`--touch-min`), `--text-body` — cumple el mínimo táctil sin depender del padding
- `.btn-xl` — `min-height: 52px`, `1rem`
- `.btn-block` — `width: 100%`
- `.btn-icon` — 34×34 px, circular (radius 50 %)

**Estados:**
- `:disabled`, `[aria-disabled="true"]` → `opacity: 0.35`, `cursor: not-allowed`, sin transform.
- `[data-state="loading"]` → `pointer-events: none`, `opacity: 0.7`. El `.btn-label` baja a `0.6` para dejar sitio al spinner. **El botón conserva su ancho** para que la fila no salte.

### 9.3 Formularios

Los inputs usan `--bg-app` en reposo para distinguirse de la tarjeta blanca que los contiene, y pasan a blanco con ring al enfocar.

- `.field` — flex column, gap `--space-1`, `margin-bottom: --space-4`.
- `.field > label` — `--text-micro`, peso 600, uppercase, tracking `--tracking-label`, color secondary.
- `.field-row` — grid 2 columnas, gap `--space-3`.

**Inputs** (`input`, `select`, `textarea`): `width: 100%`, `min-height: --touch-min`, padding `--space-3 --space-4`, `--text-body-sm`, bg `--bg-app`, border 1px transparent, `radius-md`. Hover → `--bg-pressed`. Foco → bg `--bg-surface`, `box-shadow: 0 0 0 2px --brand-tint-35`.

| Estado | Estilo |
|---|---|
| Reposo | bg `--bg-app`, border transparente |
| Hover | bg `--bg-pressed` |
| Foco | bg `--bg-surface`, ring 2 px `--brand-tint-35` |
| Disabled | `opacity: 0.5`, `cursor: not-allowed` |
| Error (`aria-invalid="true"`) | bg `--bg-surface`, ring 2 px `--danger-tint`, border `--danger` |
| Success (`.is-success`) | border `--success` |

`.field-hint` (caption, secondary) y `.field-error` (caption, danger, peso 500, `min-height: 1.25em` para reservar espacio). **Nunca un código de error crudo.**

**Switch** (configuración de notificaciones): track 44×26 px, `radius-pill`, bg `rgba(0,0,0,0.10)`, knob 22 px blanco con `--shadow-hairline`. Checked → bg `--success`, knob `translateX(18px)`. Foco visible → outline 2 px brand.

**Select** con flecha SVG inline (stroke `#6e6e73`), `appearance: none`, padding-right `--space-8`.

### 9.4 Superficies (cards)

`.card` — bg `--bg-surface`, `radius-lg`, `--shadow-hairline`. Hover → `--shadow-raised`. `.card--flat` no eleva en hover.

- `.card-pad` — padding `--space-5`
- `.card-pad-lg` — padding `--space-7`
- `.card-header` — flex space-between, padding `--space-4`, border-bottom `--border`
- `.card-body` — padding `--space-4`
- `.card-footer` — padding `--space-4`, border-top `--border`
- `.divider` — height 1 px, bg `--border`

### 9.5 Badges de estado

Un badge = un estado. **Nunca texto libre.**

Base `.badge`: inline-flex, padding `2px --space-2`, `radius-xs`, `--text-micro`, peso 600, uppercase, tracking `--tracking-wide`. `.badge--pill` → `radius-pill`, padding `3px --space-3`, sin uppercase.

| Clase | Fondo | Texto | Uso |
|---|---|---|---|
| `.badge-ok` / `.badge-active` / `.badge-approved` | `--success-tint` | `--success-strong` | Éxito |
| `.badge-late` | `--brand-tint-12` | `--brand` | Retraso |
| `.badge-incident` / `.badge-rejected` | `--danger-tint` | `--danger` | Incidente, rechazado |
| `.badge-inactive` | `rgba(0,0,0,0.06)` | `--text-secondary` | Inactivo |
| `.badge-pending` | `--warning-tint` | `--warning-strong` | Pendiente |
| `.badge-on-leave` | `--info-tint` | `--info` | De baja |
| `.badge-syncing` | `--warning-tint` | `--warning-strong` | Sincronizando (dot con `tu-pulse`) |

**Regla de forma:** la pastilla (`--pill`) se usa para presencia en vivo; el rectángulo (`--xs`) para estados de fila en tabla, donde la pastilla compite con el texto.

`.dot` — 6×6 px, radius 50 %, `background: currentColor`.

`.presence` — indicador de conexión en navbar: padding `4px --space-3`, `--text-micro`, bg `--success-tint`. `.presence.is-offline` → bg `rgba(0,0,0,0.05)`, texto secondary.

### 9.6 Tablas

Densidad alta pero legible: padding `--space-3 --space-4`. El gerente quiere ver todo su equipo de un vistazo, no una tarjeta por empleado.

- `thead th` — `--text-micro`, peso 600, uppercase, tracking `--tracking-label`, color secondary, border-bottom `--border`, `white-space: nowrap`.
- `tbody td` — `--text-caption`, color primary, border-bottom `--border-hairline`, `vertical-align: middle`.
- `tbody tr:hover td` → bg `rgba(0,0,0,0.02)`.
- `.table-scroll` — `overflow-x: auto`, `min-width: 620px`.
- `.cell-num` — `text-align: right`, `tabular-nums`.
- `.cell-actions` — `text-align: right`, `white-space: nowrap`.

### 9.7 Estado vacío

Una tabla o panel nunca se queda simplemente en blanco.

`.empty-state` — flex column center, gap `--space-3`, padding `--space-12 --space-6`, texto centrado. Icono en `--text-quaternary` (SVG 48 px, stroke 1.5). Título `--text-body` peso 600. Descripción `--text-body-sm`, secondary, `max-width: 42ch`. Botón con `margin-top: --space-2`.

### 9.8 Carga — skeleton, no spinner infinito

En pantallas de datos el skeleton comunica la forma de lo que viene; el spinner solo comunica espera. **El spinner sobrevive únicamente dentro de botones**, donde no hay forma que anticipar.

- `.skeleton` — bg `rgba(0,0,0,0.04)`, `radius-xs`, `color: transparent !important`, `user-select: none`. `::after` con gradiente blanco y `tu-shimmer` 1.4s.
- `.skeleton-text` (height `0.75em`), `.skeleton-line` (12 px), anchos `.skeleton-w-40/60/80`.
- `.spinner` — 16×16 px, border 2 px `rgba(255,255,255,0.35)`, `border-top-color: currentColor`, `tu-spin` 0.6s linear.

### 9.9 Toast

`.toast-container` — fixed top-right, `z-index: --z-toast`, column gap `--space-2`, `max-width: 340px`, `pointer-events: none`.

`.toast` — flex, padding `--space-3 --space-4`, `radius-md`, `--text-caption`, texto `--text-on-brand`, `--shadow-modal`, animación `tu-slide-in` (slow), `pointer-events: auto`. Salida: `.toast-out` con `tu-slide-out` forwards.

Variantes: `.toast-success` (`--success-strong`), `.toast-error` (`--danger`), `.toast-warning` (`--warning-strong`), `.toast-info` (`--info`).

### 9.10 Modal

`.modal-overlay` — fixed inset 0, `z-index: --z-modal`, flex center, padding `--space-5`, bg `--bg-scrim`, `backdrop-filter: blur(4px)`, animación `tu-fade-in` (fast).

`.modal` — `max-width: 500px` (`.modal-wide` 620px), `max-height: 85vh`, overflow-y auto, `--bg-surface`, `radius-xl`, `--shadow-modal`, animación `tu-rise`.

- `.modal-header` — sticky top, flex space-between, padding `--space-4 --space-5`, border-bottom `--border`.
- `.modal-body` — padding `--space-5`.
- `.modal-footer` — sticky bottom, flex flex-end, gap `--space-2`, padding `--space-4 --space-5`, border-top `--border`.
- `.modal-close` — 32×32 px, `radius-sm`, color secondary. Hover → bg `--bg-hover`, texto primary.

### 9.11 Navegación

`.nav-item` — flex, gap `--space-3`, `min-height: --touch-min`, padding `--space-2 --space-3`, `radius-sm`, `--text-caption`, color secondary. Hover → bg `--bg-hover`, texto primary. `.active` → bg `--brand-tint-08`, texto `--brand`, peso 500, icono opacidad 1.

`.tabs` — flex, border-bottom `--border`. `.tab` — padding `--space-2 --space-4`, `min-height: --touch-min`, border-bottom 2 px transparent, `margin-bottom: -1px`. `.active` → color `--brand`, border-bottom `--brand`, peso 500. `.tab-panel` oculto salvo `.active`.

`.segmented` (selector de idioma) — inline-flex, padding 2 px, bg `rgba(0,0,0,0.04)`, `radius-pill`. Botón activo → bg `--bg-surface`, texto `--brand`, `--shadow-hairline`.

### 9.12 Banners

`.banner` — flex center, gap `--space-2`, padding `--space-2 --space-4`, `--text-caption`, peso 500. `.banner-demo` → bg `--warning`, texto blanco. `.banner-offline` → bg `--warning-tint`, texto `--warning-strong`.

---

## 10. Estados (resumen de patrones)

Todos los componentes comparten el mismo modelo de estados, basado en los tokens semánticos:

| Estado | Color | Patrón |
|---|---|---|
| Default / Reposo | Neutro | Superficie base, borde transparente |
| Hover | Neutro | bg `--bg-hover` o tinte de marca sutil |
| Pressed | Neutro | bg `--bg-pressed` o `--brand-pressed` |
| Foco | Marca | outline 2 px `--brand` (offset 2 px) o ring `--brand-tint-35` |
| Activo / seleccionado | Marca | bg `--brand-tint-08/12`, texto `--brand` |
| Disabled | Neutro | `opacity: 0.35` (botón) / `0.5` (input), `cursor: not-allowed` |
| Loading | Neutro | `opacity: 0.7`, `pointer-events: none`, spinner |
| Éxito | `--success` | tinte + `-strong` para texto |
| Error | `--danger` | tinte + base para texto/borde |
| Advertencia | `--warning` | tinte + `-strong` para texto |
| Offline / syncing | `--warning` | **nunca `--danger`**: no sincronizado todavía no es un error, es transitorio |

---

## 11. Microinteracciones

- **Botón pressed:** `scale(0.97)` en `--dur-fast` (`--ease-out`). Feedback inmediato, sin rebote.
- **Card hover:** `--shadow-hairline` → `--shadow-raised` en `--dur-base`.
- **Input focus:** bg `--bg-app` → `--bg-surface` + ring 2 px `--brand-tint-35`.
- **Switch:** knob `translateX(18px)` en `--dur-base`, bg track → `--success`.
- **Nav active:** tinte `--brand-tint-08` + texto `--brand`, icono opacidad 0.6 → 1.
- **Tab active:** border-bottom 2 px `--brand` con color de texto.
- **Skeleton shimmer:** gradiente blanco 1.4s `--ease-in-out` infinito.
- **Dot de syncing:** `tu-pulse` 1.6s (opacity 1 → 0.35 → 1).
- **Toast:** `tu-slide-in` (translateX 16px → 0) en `--dur-slow`; salida `tu-slide-out` forwards.
- **Modal:** overlay `tu-fade-in` (fast) + modal `tu-rise` (translateY 8px → 0) en `--dur-base`.
- **Reveal on scroll:** `.js .reveal` parte de `opacity: 0` + `translateY(12px)` y pasa a visible al añadir `.is-visible` (IntersectionObserver). **Sin JS el contenido es visible por defecto** — el reveal es progresivo, no bloqueante.
- **Foco visible:** `outline: 2px solid --brand; outline-offset: 2px; border-radius: --radius-xs`. **Nunca se anima**: aparece en el mismo frame en que el usuario pulsa Tab. `:focus:not(:focus-visible)` se elimina para no ensuciar el clic.

---

## 12. Accesibilidad

### 12.1 Foco y teclado

- `:focus-visible` con outline 2 px `--brand` y offset 2 px en **todo elemento interactivo**.
- Skip-link (`--text-caption`, peso 600, `--shadow-modal`) fuera de pantalla (`top: -100px`) que aparece al recibir foco (`top: --space-4`). z-index por encima de toast.
- Targets táctiles `≥ 44px` (`--touch-min`), `≥ 60px` en kiosco.

### 12.2 Medios preferidos

- **`prefers-reduced-motion: reduce`** — `scroll-behavior: auto`, animaciones y transiciones a `0.01ms`, reveal visible, skeleton sin shimmer. El movimiento espacial se sustituye por presencia inmediata, no se pierde el contenido.
- **`prefers-contrast: more`** — refuerza `--text-secondary` a `#4a4a4f`, `--border` a `rgba(0,0,0,0.14)`, `--border-strong` a `rgba(0,0,0,0.24)`.
- **`prefers-color-scheme: dark`** — `color-scheme: light` forzado. No hay modo oscuro por decisión de producto.

### 12.3 Otros

- `::selection` con `--brand-tint-12` y texto primary.
- `.sr-only` para texto solo de lectores de pantalla.
- Scrollbar de 6 px, thumb `rgba(0,0,0,0.12)`, hover `rgba(0,0,0,0.2)`.
- `-webkit-font-smoothing: antialiased` y `-moz-osx-font-smoothing: grayscale`.
- Print: oculta `.no-print`, `.toast-container`, `#sidebar`, `#navbar`; las cards pierden sombra y toman borde `--border-strong`.

---

## 13. Reglas de uso

1. **Una sola acción primaria por pantalla.** No se codifica en CSS, pero la secundaria nunca compite visualmente.
2. **El naranja nunca es fondo de superficie grande.** Solo acento, botones, enlaces, foco, tintes sutiles.
3. **Sin gradientes decorativos ni sombras dramáticas.** Una sola familia de sombras, tope 0.08 alpha.
4. **Ningún valor fuera de los tokens.** Si un color, radio o espacio no está en `:root`, no existe. No se hardcodea.
5. **Tabular nums en toda cifra en vivo.** `.tabular`, `.stat-card-value`, `.clock-live`.
6. **Skeleton en pantallas de datos, spinner solo en botones.** El spinner infinito fuera de un botón es un anti-patrón.
7. **Estado vacío obligatorio.** Una tabla o panel nunca se queda en blanco.
8. **Un badge = un estado.** Nunca texto libre dentro de un badge.
9. **Offline es `--warning`, nunca `--danger`.** No sincronizado todavía no es un error.
10. **Errores en lenguaje humano, nunca códigos crudos.** `.field-error` siempre con mensaje legible.
11. **La escala de marketing solo en landing.** `--text-hero`, `--text-section`, `--text-lead` no entran en el dashboard.
12. **Foco visible nunca animado.** Aparece en el mismo frame del Tab.
13. **El reveal progresa, no bloquea.** Sin JS, el contenido es visible por defecto.
14. **El logo no se comprime por debajo de 24 px.** A favicon se suelta el arco exterior.
15. **El botón en loading conserva su ancho.** La fila no salta.

---

## 14. Referencia rápida de tokens

```
/* Colores */
--brand #FF6B35 · --brand-hover #E55A2B · --brand-pressed #CC4E22
--text-primary #1d1d1f · --text-secondary #6e6e73 · --text-on-brand #fff
--bg-app #f5f5f7 · --bg-surface #fff · --bg-sunken #fafafa
--success #34C759 · --success-strong #248A3D · --danger #FF3B30
--warning #FF9500 · --warning-strong #B25E00 · --info #007AFF

/* Tipografía */
--text-display 34px · --text-h1 22px · --text-h2 18px · --text-body 15px
--text-hero clamp(36→56px) · --text-section clamp(28→40px) · --text-lead clamp(17→20px)

/* Espaciado (4pt) */
--space-1 4 · --space-2 8 · --space-3 12 · --space-4 16 · --space-5 20
--space-6 24 · --space-8 32 · --space-12 48 · --space-16 64 · --space-20 80

/* Radios */
--radius-xs 4 · --radius-sm 6 · --radius-md 8 · --radius-lg 10 · --radius-xl 12 · --radius-2xl 16 · --radius-pill 980px

/* Movimiento */
--dur-instant 100ms · --dur-fast 150ms · --dur-base 200ms · --dur-slow 300ms
--ease-out cubic-bezier(0.16,1,0.3,1) · --ease-in cubic-bezier(0.4,0,1,1)

/* Layout */
--touch-min 44px (kiosco 60px) · --container 1100px · --measure 68ch
--z-modal 100 · --z-toast 200
```

---

*Documento generado el 8 de agosto de 2026. Fuente de verdad: `design_system.css`. Cualquier divergencia entre esta guía y el CSS, el CSS gana.*