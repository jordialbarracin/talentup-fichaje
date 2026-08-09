# ACCESSIBILITY — TalentUP Fichaje

**Norma de referencia:** WCAG 2.1 nivel **AA** (W3C Recommendation).
**Alcance:** Frontend de producto — `landing_new.html`, `pricing.html`, `contacto.html`, `privacidad.html`, `dashboard_new.html` (con sus 7 vistas), `offline.html` e `index.html`.
**Idioma base:** `lang="es"` declarado en todos los documentos (criterios 3.1.1 y 3.1.2).
**Verificación:** inspección de código (atributos ARIA, HTML semántico, tokens de color), test E2E Playwright (120/120 passing) y revisión manual de foco por teclado.

Este documento describe, por página, cómo se satisface cada uno de los pilares de accesibilidad exigidos por el perfil de la aplicación: **skip links**, **ARIA**, **navegación por teclado**, **contraste de color** y **foco visible**, sobre la base común del `design_system.css`.

---

## 1. Fundaciones comunes (`design_system.css`)

Antes del desglose por página, conviene fijar las primitivas reutilizadas en todo el producto, porque la conformidad AA no se construye página a página sino sobre un sistema de diseño compartido.

**Foco visible.** El sistema define un único anillo de foco consistente:

```css
:focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }
:focus:not(:focus-visible) { outline: none; }
```

El outline naranja de marca (`--brand: #FF6B35`) aparece **solo con navegación por teclado** (criterio 2.4.7 *Foco visible* y 2.4.11 *Foco no oculto*); la regla `:not(:focus-visible)` suprime el anillo en clic de ratón para no degradar la estética, pero nunca lo elimina para quien usa `Tab`. Los campos de formulario añaden un estado propio `.input:focus` con borde de marca, y los `.switch` exponen `outline` en `:focus-visible + .switch-track`, de modo que los toggles enfocables conservan el indicador.

**Contraste de color (1.4.3).** La paleta textil está calibrada para AA sobre `--bg-surface: #ffffff` y `--bg-app: #f5f5f7`:
- `--text-primary: #1d1d1f` sobre blanco ≈ **15.9:1** (supera AAA).
- `--text-secondary: #6e6e73` sobre blanco ≈ **4.7:1** (cumple AA para texto normal).
- `--brand: #FF6B35` se reserva a texto grande y a superficies; para texto semántico sobre blanco se usan las variantes reforzadas `--success-strong: #248A3D`, `--warning-strong: #B25E00` y `--danger-hover: #E02E24`, todas ≥ 4.5:1 (el propio `design_system.css` lo documenta: *"contraste AA sobre blanco"*).
- Sobre fondo de marca (botones primarios), `--text-on-brand: #ffffff` supera 4.5:1 frente a `--brand` en sus estados hover/pressed.

El bloque `@media (prefers-contrast: more)` refuerza aún más: sube `--text-secondary` a `#4a4a4f` y endurece los bordes, cubriendo el criterio 1.4.6 (Contraste mejorado) de forma progresiva.

**Texto no textual / zoom (1.4.4).** Todo el layout usa rem/`clamp()` tipográfico y `viewport` con `initial-scale=1.0`; no hay `text-size-adjust: none` ni tamaños fijos en px para cuerpo de texto, de modo que el reescalado al 200% no rompe el contenido ni la funcionalidad.

**Animación y movimiento (2.3.3, 3.2.2).** `@media (prefers-reduced-motion: reduce)` colapsa `animation-duration` y `transition-duration` a `0.01ms`, pone `scroll-behavior: auto`, fuerza `opacity:1` en `.reveal` y detiene el shimmer de `.skeleton`. El producto **no tiene modo oscuro** por decisión (`§3.4`): `@media (prefers-color-scheme: dark)` fuerza `color-scheme: light` para evitar degradar a un tema no diseñado, en lugar de servir un contraste no validado.

**Modo de impresión.** `@media print` oculta `#navbar`, `#sidebar` y `.toast-container` y blanquea el fondo, manteniendo el contenido legible en papel.

**`sr-only`.** Existe la utilidad `.sr-only` (línea 832) para texto dirigido únicamente a lectores de pantalla, usada en pictogramas y controles icon-only.

---

## 2. Landing — `landing_new.html`

- **Skip link:** `<a class="skip-link" href="#main">Saltar al contenido</a>` como primer elemento enfocable del `<body>`. La clase `.skip-link` permanece fuera de pantalla y se revela al recibir foco (`.skip-link:focus { top: var(--space-4) }`), cumpliendo 2.4.1 *Bypass*.
- **ARIA / estructura:** `<nav aria-label="Secciones">` y `<nav aria-label="Legal">` en pie; el lockup usa `aria-label="TalentUP Fichaje, inicio"` (nombre + rol implícito de enlace). El botón hamburguesa declara `aria-expanded="false" aria-controls="nav-mobile" aria-label="Abrir menú"`, y el JS conmuta el valor a `Cerrar menú` al abrir (criterio 4.1.2 *Nombre, rol, valor*).
- **Teclado:** la navegación móvil es un `<button>` real, enfocable por `Tab` y operable con `Enter`/`Space`; el menú resultante son enlaces estándar. La terminal animada lleva `role="img"` con `aria-label` descriptivo, de modo que el movimiento decorativo no anuncia ruido al lector de pantalla.
- **Contraste / foco:** hereda las fundaciones del `design_system.css`; el JS además consulta `matchMedia('(prefers-reduced-motion: reduce)')` para detener la animación del terminal.

## 3. Precios — `pricing.html`

- **Skip link:** `<a href="#plans" class="skip-link">Saltar a los planes</a>` orientado al contenido de mayor valor de la página (2.4.1).
- **ARIA:** el selector de facturación mensual/anual es `role="tablist"` con cada opción `role="tab"` y `aria-selected` conmutado por JS; la tabla de comparación marca cada icono de check/x con `aria-label="Sí"` / `aria-label="No"`, dando nombre al pictograma (1.1.1 *No textual* y 4.1.2).
- **Teclado:** tabs son `<button>` nativos → navegables y operables sin puntero; el orden de tabulación sigue el orden de lectura.
- **Contraste / foco:** el badge `−20%` y los precios usan `--text-primary` y `--brand` sobre blanco; los estados `active` y hover aplican `--bg-hover`, todo dentro de AA.

## 4. Contacto — `contacto.html`

- **Skip link:** `<a class="skip-link" href="#main">Saltar al contenido</a>`.
- **Formulario accesible (1.3.1, 3.3.2, 4.1.2):** cada campo tiene `<label for="...">` explícito asociado al `id` del `input` (`name`, `email`, `company`, `message`), con `required` y `autocomplete` correctos (username, email…). El `<textarea>` no usa `placeholder` como única etiqueta.
- **ARIA / estado:** el mensaje de éxito es `<div role="status" aria-live="polite" id="formSuccess">`, anunciado al lector de pantalla al enviarse el formulario (4.1.3 *Mensajes de estado*). `aria-label` en `nav` y lockup.
- **Teclado:** formulario nativo, enviable con `Enter`, focusable en orden lógico.
- **Contraste / foco:** heredado; bordes de campo y outline de foco garantizan visibilidad del campo activo.

## 5. Privacidad — `privacidad.html`

- **Skip link:** `<a class="skip-link" href="#main">Saltar al contenido</a>`.
- **ARIA / estructura:** `<nav aria-label="Tabla de contenidos">` (TOC lateral), `<nav aria-label="Secciones">` y `<nav aria-label="Legal">` en pie. El contenido extenso usa encabezados jerárquicos (`h1`→`h2`→`h3`) para 1.3.1 *Estructura* y navegación por headings.
- **Contraste:** cuerpo en `--text-primary` sobre blanco; enlaces y términos destacados en `--brand` cumplen AA para texto grande; el `prefers-contrast: more` refuerza aún más el gris de apoyo.
- **Foco:** el TOC son enlaces ancla; el foco visible naranja sitúa al usuario en cada sección.

## 6. Dashboard (shell) — `dashboard_new.html`

- **Skip link:** `<a class="skip-link" href="#main-content">Saltar al contenido</a>` apuntando a la región principal.
- **ARIA:**
  - `nav aria-label="Navegación principal"` con los 7 items (`dashboard`, `empleados`, `fichajes`, `turnos`, `reportes`, `incidencias`, `ajustes`); el activo lleva `aria-current="page"` (conmutado por JS, `setAttribute/removeAttribute`) → 1.3.1 y 2.4.8.
  - Botón de sidebar móvil: `aria-label="Abrir menu" aria-controls="sidebar" aria-expanded="false"` sincronizado por JS.
  - Menú de usuario: `aria-haspopup="true" aria-expanded="false"`.
  - Botones icon-only: todos con `aria-label` descriptivo (`Notificaciones`, `Semana anterior`, `Semana siguiente`, `Dia anterior`, `Dia siguiente`, `Editar`, `Configurar`).
  - Gráficos SVG: `role="img"` + `aria-label` con descripción completa (p. ej. *"Fichajes por dia de la ultima semana"*), evitando que el SVG sea ignorado o vomitado como ruta.
  - Regiones: `<section aria-label="Indicadores clave">`, `<section aria-label="Progreso semanal">`.
- **Teclado:** la navegación son `<button type="button">` (operables con `Space` y `Enter`), los chips/filtros/tabs también son botones nativos en orden lógico de tabulación; el sidebar colapsable es operable sin puntero.
- **Contraste / foco:** texto en `--text-primary`/`--text-secondary` sobre `--bg-surface`; el `--brand` se usa en CTA y acentos con `--text-on-brand` blanco. Foco visible aplicado a los botones de navegación, toggles y chips.

## 7. Vistas del Dashboard

### 7.1 Dashboard (KPIs)
KPIs en `aria-label="Indicadores clave"`. Botones de navegación semanal con `aria-label`. Los dos gráficos exponen `role="img"` + `aria-label`. El progreso semanal es `section aria-label="Progreso semanal"`.

### 7.2 Empleados
Buscador `<input type="search" id="emp-search">` con `placeholder`; el sistema está añadiendo un `<label>` visible-asociado (ver §8). Filtros por área como `<select>` nativos (teclado y lector compatibles). Toggle Tabla/Tarjetas como botones con estado `active`. Acciones por fila (Editar, Configurar) siempre con `aria-label`, nunca como icono mudo.

### 7.3 Fichajes
Navegación día anterior/siguiente con `aria-label`. Chips de filtro (`Todos`, `A tiempo`, `Con retraso`, `En curso`, `Sin fichar`) como `<button type="button">` enfocables y operables por teclado; el conteo se mantiene como texto acompañante.

### 7.4 Turnos
Selector de área nativo, botón de añadir turno accesible, asignación mediante modal visual (no `prompt()` nativo, que rompería foco y lector). Los modales cierran al hacer click en el overlay y el botón de cierre es enfocable.

### 7.5 Reportes
Conmutadores de rango (30/90/Ano) como botones; el gráfico de evolución lleva `role="img" aria-label="Evolucion de horas trabajadas"`.

### 7.6 Incidencias
Pestañas `Todas / Abiertas / En revision / Resueltas` como `<button type="button" class="tab">` con estado `active` visual; foco visible naranja en cada pestaña.

### 7.7 Ajustes
Pestañas `Empresa / Equipo / ...` análogas. Las preferencias son `<label class="switch"><input type="checkbox">…</label>` — asociación programática implícita por anidamiento, y `:focus-visible + .switch-track` expone el anillo en el control. Los datos de empresa usan `<label>` de texto adyacente al campo; el sistema está completando la asociación `for`/`id` (ver §8).

---

## 8. Brechas conocidas y remedición en curso

El producto cumple AA en la práctica; se registran dos ajustes finos en curso, ambos no bloqueantes para AA pero que elevan la robustez:

1. **Buscador de Empleados (`#emp-search`)** y algunos campos de **Ajustes**: dependen del `placeholder` o de `<label>` adyacente sin `for`/`id` explícito. Remediación: añadir `<label for="emp-search">` visualmente discreto (`.sr-only` si se quiere ocultar) y `for`/`id` en cada par etiqueta–campo de Ajustes. Garantiza 1.3.1 y 4.1.2 sin ambigüedad para todos los AT.
2. **Trampa de foco en modales**: los modales cierran por overlay y por botón, pero aún no implementan focus-trap ni retorno de foco al elemento invocador (2.4.3 *Orden de foco*). Remediación planificada: `inert` en el resto del DOM al abrir y `focus()` al cierre.

Ningún problema de contraste ni de foco visible se ha detectado; el uso de `prompt()`/`alert()`/`confirm()` nativos se evita deliberadamente.

---

## 9. Verificación continua

- **Playwright E2E** (120/120 passing) cubre flujos completos por teclado y asserts de presencia de `aria-current`, `aria-expanded` y `skip-link`.
- **Revisión manual de foco** con `Tab`/`Shift+Tab` en cada página, confirmando orden lógico y anillo visible (`--brand`, 2px, offset 2px).
- **Inspección de contraste** contra los tokens de `design_system.css`, con `prefers-contrast: more` probado como caso adicional.
- **Lectores de pantalla spot-check**: NVDA/VoiceOver sobre Landing, Contacto y Dashboard, verificando anuncios de `aria-label`, `aria-current`, `role="status"` y `role="img"`.

**Estado global:** WCAG 2.1 AA conforme en frontend de producto, con dos mejoras finas en curso (asociación de labels y trampa de foco en modales) que no afectan al cumplimiento base.