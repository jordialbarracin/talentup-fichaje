# Documento de Actualización — TalentUP Fichaje

**Versión:** 2.0 · **Fecha:** 2026-08-09 · **Dominio:** `talentup.es`

Este documento describe cómo se mantiene el frontend de TalentUP Fichaje vivo, coherente y versionado a lo largo del tiempo. Cubre cuatro flujos de cambio que conviven en el mismo código: la incorporación de nuevas *features*, la creación de nuevos componentes de UI, la extensión del sistema de design tokens y el gobierno de versiones mediante el changelog. El frontend es un conjunto de **páginas HTML estáticas** servidas por Vercel, sin framework de build ni SSR. No hay *bundler*, no hay *tree-shaking*, no hay *hot reload* de React. Eso simplifica el deploy, pero traslada toda la disciplina de mantenimiento a tres archivos centrales: `design_system.css`, `STYLE_GUIDE.md` y `COMPONENT_GUIDE.md`, anclados por un `CHANGELOG_v2.md` que es la crónica oficial de cada release.

---

## 1. Filosofía de mantenimiento

El frontend de TalentUP se sostiene sobre una idea simple: **un solo sistema de diseño, cuatro superficies** (landing, dashboard, PWA móvil y terminal kiosco). Cualquier cambio visual o estructural se origina en `frontend/design_system.css` (894 líneas, 35 KB), la única fuente de verdad de tokens y componentes. Las ocho páginas del producto importan este archivo y consumen sus variables; ninguna declara colores, radios o espacios sueltos.

Esta arquitectura hace que mantener el frontend sea, en la práctica, mantener tres cosas:

1. **Tokens** en `:root` de `design_system.css` — cualquier ajuste de marca, accesibilidad o densidad se hace aquí y se propaga solo.
2. **Componentes** en el mismo archivo (18 secciones) — cada clase nueva o modificada se documenta en `COMPONENT_GUIDE.md` antes de llegar a producción.
3. **Páginas** — consumen tokens y componentes; no aportan estilos propios salvo composición.

El principio rector, recogido en `STYLE_GUIDE.md` (sección 13), es tajante: *si un color, radio o espacio no está definido en `:root`, no existe*. No se hardcodea. Esta regla es lo que permite que el sistema escale sin degradarse: un nuevo botón, una nueva tarjeta o un nuevo badge se construyen con los tokens existentes, y si hace falta un token nuevo, se añade con nombre y se documenta.

---

## 2. Incorporar nuevas features

Una *feature* frontend en TalentUP suele ser una nueva vista del dashboard, una nueva página pública o un flujo nuevo en la PWA móvil. El procedimiento es siempre el mismo:

1. **Definir la ruta y el archivo físico.** Las páginas públicas (marketing/legales) se sirven como HTML estático en Vercel con redirecciones limpias en `vercel.json`. Las vistas del dashboard son secciones internas de la SPA `index.html`, conmutadas por la función `navigate(page)` con `data-page`; no usan router de URL. Una nueva vista del dashboard no crea un archivo nuevo, añade un `<section data-page="...">` al HTML existente y su lógica en `src/app.js` (125 KB).

2. **Consumir tokens y componentes existentes.** La feature se construye con `.btn`, `.card`, `.field`, `.badge`, `.table-scroll`, `.empty-state` y similares. Si la feature introduce un patrón visual que no existe (por ejemplo, un calendario de turnos), se evalúa si merece convertirse en componente del sistema o si es composición puntual de los existentes.

3. **Conectar la API con `credentials: 'include'`.** Las llamadas son siempre relativas (`/api/...`) en producción; el proxy de Vercel enruta hacia el backend en Railway. En desarrollo, `API_BASE` se resuelve a `http://localhost:8080/api`. Los endpoints públicos de fichaje (`/api/clock*`, `/api/tenants`) no requieren JWT; los de gestión sí, pero viajan como cookies httpOnly que la SPA nunca lee en JS.

4. **Cubrir loading, error y vacío.** Toda pantalla de datos tiene skeleton (no spinner infinito), estado de error con mensaje humano (nunca código crudo) y `.empty-state` con icono, título, descripción y acción. Estas tres cubiertas son obligatorias; una vista que muestra una tabla en blanco no se acepta.

5. **Registrar en el changelog.** La feature se documenta en la sección *Añadido* de la próxima versión de `CHANGELOG_v2.md`, indicando archivo, líneas y propósito.

---

## 3. Añadir nuevos componentes

El catálogo de componentes vive en `design_system.css` y se documenta en `frontend/COMPONENT_GUIDE.md` (735 líneas). Cada componente tiene cuatro partes: clase CSS, variaciones, *cuándo usar* y *cuándo NO usar*, más un snippet HTML listo para copiar.

El flujo para añadir un componente nuevo es:

1. **Justificar la necesidad.** Un componente nuevo se crea cuando un patrón se repite en al menos dos páginas y no se resuelve con composición de los existentes. No se crean variantes unicas (one-off) como componentes del sistema; esas quedan en el HTML de la página.

2. **Definir el nombre y la clase.** Convención: `.btn`, `.card`, `.badge`, `.field`, `.toast`, `.nav-item`. Las variantes se separan con `--`: `.btn-primary`, `.card-pad`, `.badge--pill`. Los estados se expresan con clases de estado (`.active`, `.is-success`) o atributos (`aria-invalid="true"`, `data-state="loading"`), nunca con selectores ad-hoc.

3. **Construir con tokens.** El componente se escribe con `--brand`, `--space-4`, `--radius-lg`, `--shadow-card`, `--dur-base` y demás. Cualquier valor hardcodeado es un defecto: o se introduce como token nuevo (ver sección 4), o se reconsidera el diseño.

4. **Documentar el componente en `COMPONENT_GUIDE.md`.** Se añade una sección con tabla de variaciones, criterios de uso, anti-patrones y ejemplo HTML. La regla es que ningún componente llega a producción sin su entrada en la guía: si no está documentado, no existe oficialmente.

5. **Probar accesibilidad.** Todo componente interactivo tiene `:focus-visible` con outline 2 px `--brand`, target táctil ≥ 44 px (≥ 60 px en kiosco) y comportamiento en `prefers-reduced-motion`. Los tests E2E de Playwright (120 passing) cubren foco, contraste y teclado; un componente nuevo añade sus propios casos.

6. **Actualizar el changelog.** Se registra el componente, sus variaciones y el número de líneas añadidas a `design_system.css`.

---

## 4. Extender los design tokens

Los tokens se definen en `:root` de `design_system.css` y se agrupan en categorías: color, tipografía, espaciado, radios, sombras, movimiento, layout y z-index. La guía de referencia rápida está en `STYLE_GUIDE.md` (sección 14).

Para añadir o modificar un token:

1. **Evaluar la categoría.** Si es un color semántico nuevo (por ejemplo, un estado de *info* reforzado), se definen las tres variantes que el sistema exige: base, `-strong` (contraste AA sobre blanco) y `-tint` (fondo contextual). Si es un espacio, debe caer en la escala de 4 pt; no se permiten valores fuera de la escala. Si es una duración, debe pertenecer a `--dur-instant/fast/base/slow`.

2. **Nombrar con convención.** Los tokens siguen un patrón `--{categoría}-{propiedad}`: `--brand-hover`, `--text-body-sm`, `--space-6`, `--radius-xl`, `--shadow-raised`, `--dur-base`, `--z-modal`. Los tintes se nombran `--{color}-tint-{alpha}` (por ejemplo, `--brand-tint-08`).

3. **Actualizar la guía de estilo.** `STYLE_GUIDE.md` lleva la paleta completa en tablas (token, HEX, uso). Un token sin entrada en la tabla es un token que el equipo no encontrará después. La sección 14 (*referencia rápida*) se actualiza con el resumen compacto.

4. **Verificar el contraste AA.** Los colores de texto sobre blanco usan las variantes `-strong` (`success-strong #248A3D`, `warning-strong #B25E00`). Un token nuevo de texto se valida con un contrast checker antes de entrar; el test de accesibilidad E2E lo confirma.

5. **Considerar el service worker.** Los tokens de marca (`--brand`, `--bg-app`, `--text-primary`) también se reflejan en el fallback offline de `sw_v2.js` y en `manifest_v2.json` (`theme_color`). Un cambio de marca afecta a los tres sitios; se actualizan juntos.

6. **Versionar la cache.** `sw_v2.js` usa un cache versionado (`talentup-fichaje-v2`). Un cambio significativo en `design_system.css` puede requerir bump de versión de cache para forzar la invalidación en los clientes instalados. Se documenta en el changelog.

---

## 5. Versionado y changelog

El proyecto sigue **[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)** con versionado semántico `MAJOR.MINOR.PATCH`. La crónica oficial es `CHANGELOG_v2.md`, que sustituyó al `CHANGELOG.md` inicial con el release 2.0.0 del 8 de agosto de 2026.

### 5.1 Categorías de cambio

Cada release documenta cambios en cuatro bloques:

- **Añadido** — nuevas features, componentes, tokens, páginas, assets.
- **Cambiado** — modificaciones de comportamiento o de archivos existentes.
- **Corregido** — bugs resueltos.
- **Notas** — aclaraciones, decisiones de diseño, excepciones.

### 5.2 Ritmo de releases

- **PATCH** (2.0.1, 2.0.2…): correcciones de bugs, ajustes de tokens, sin cambios de API ni de estructura. No requieren nueva versión de cache del service worker.
- **MINOR** (2.1.0): nuevas features, vistas del dashboard, componentes, tokens. Requieren bump de cache y entrada completa en el changelog.
- **MAJOR** (3.0.0): cambios de arquitectura, rediseño del design system o ruptura de contrato. El paso de 1.x a 2.0 fue un major: nuevo `design_system.css`, nuevo manifest, nuevo service worker, nueva landing.

### 5.3 Cómo se escribe una entrada

Cada entrada del changelog incluye: archivo afectado, número de líneas (si es relevante), propósito y referencia al documento de diseño si lo hay. Ejemplo real de 2.0.0:

> **`frontend/design_system.css`** (894 líneas, 35 KB): hoja de tokens central que es la fuente de verdad de las cuatro superficies del producto…

Las entradas de *Añadido* listan los tokens nuevos por categoría; las de *Cambiado* explican qué se modificó y por qué; las de *Corregido* citan el bug. No se mezclan categorías; cada cambio va a su bloque.

### 5.4 El changelog como contrato

El changelog no es decorativo: es el contrato entre el estado actual del frontend y el siguiente release. Antes de etiquetar una versión (`git tag v2.1.0`), se revisa que cada cambio desde el último tag esté reflejado. Si un commit introduce un token, componente o feature sin entrada en el changelog, el release se bloquea hasta que se documenta. Esta disciplina es lo que mantiene el sistema navegable seis meses después, cuando el contexto de por qué se añadió `--brand-tint-35` se ha perdido.

---

## 6. Verificación continua

Cada cambio se valida antes de llegar a `master`:

- **Lighthouse CI** en GitHub Actions: performance ≥ 90, accessibility, SEO y best practices.
- **bundlewatch**: JS ≤ 170 KB gzip, CSS ≤ 30 KB gzip. Un componente nuevo que inflará el CSS se revisa antes de mergear.
- **Playwright E2E**: 120 tests de accesibilidad y foco por teclado.
- **Revisión manual de tokens**: un `grep` rápido confirma que no quedan valores hardcodeados en las páginas.

Con estos cuatro filtros, el frontend de TalentUP se mantiene actualizable: features nuevas sin deuda visual, componentes nuevos sin duplicar esfuerzo, tokens nuevos sin romper contraste, y un changelog que cuenta la historia de cada versión.

---

*Fin del documento. ~1500 palabras.*