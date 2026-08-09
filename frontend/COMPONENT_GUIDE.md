# TalentUP Fichaje — Guía de Componentes

> **Fuente de verdad:** `design_system.css` (895 líneas). Este documento cataloga cada componente de UI definido en la hoja de estilos, con su clase CSS, variaciones, criterios de uso y ejemplo HTML listo para copiar.
>
> **Alcance:** landing · dashboard · PWA empleado · terminal kiosco. Un solo sistema, cuatro superficies.
>
> **Principios que el sistema hace cumplir por construcción:**
> 1. El naranja (`--brand: #FF6B35`) es acento, nunca fondo de superficie grande.
> 2. Claridad bajo presión: targets táctiles ≥ 44px en app, ≥ 60px en kiosco.
> 3. Confianza silenciosa: sin gradientes decorativos, sin sombras dramáticas.
> 4. Una sola acción primaria por pantalla.

---

## Tabla de contenidos

1. [Botones](#1-botones)
2. [Inputs y formularios](#2-inputs-y-formularios)
3. [Cards (superficies)](#3-cards-superficies)
4. [Tablas](#4-tablas)
5. [Badges de estado](#5-badges-de-estado)
6. [Modales](#6-modales)
7. [Toasts](#7-toasts)
8. [Navegación](#8-navegación)
9. [Skeletons y carga](#9-skeletons-y-carga)
10. [Estado vacío](#10-estado-vacío)
11. [Banners](#11-banners)
12. [Tipografía utilitaria](#12-tipografía-utilitaria)

---

## 1. Botones

**Clase base:** `.btn`

Cuatro variantes, ocho estados cada una. Una sola acción primaria por pantalla — la regla no se puede codificar en CSS, pero el diseño hace que la secundaria nunca compita visualmente con la primaria.

### Variaciones

| Clase | Uso | Fondo |
|---|---|---|
| `.btn-primary` | Acción principal de la pantalla | `--brand` (#FF6B35) |
| `.btn-secondary` | Acción alternativa coexistente | transparente, borde naranja 35% |
| `.btn-ghost` | Acciones terciarias, herramientas | transparente |
| `.btn-danger` | Acción destructiva confirmada | `--danger` (#FF3B30) |

**Tamaños:**

| Clase | Altura mínima | Notas |
|---|---|---|
| `.btn-sm` | 30px | Densidad alta (filas de tabla) |
| *(default)* | 36px | Estándar |
| `.btn-lg` | 44px (= `--touch-min`) | Móvil, kiosco ligero |
| `.btn-xl` | 52px | CTA de landing |
| `.btn-block` | — | Ocupa el 100% del ancho |
| `.btn-icon` | 34px círculo | Solo icono, `padding: 0` |

**Estados especiales:** `data-state="loading"` desactiva el botón y conserva el ancho (la fila no salta). `:disabled` / `aria-disabled="true"` reduce opacidad a 0.35.

### Cuándo usar

- **Primary:** la acción más importante de la vista ("Añadir empleado", "Guardar cambios", "Generar"). Una sola por pantalla.
- **Secondary:** una acción válida coexistente con la primaria ("Exportar", "PDF", "Excel").
- **Ghost:** herramientas contextuales ("Actualizar", navegación de semanas, edición en fila de tabla).
- **Danger:** eliminación o acción irreversible ya confirmada ("Eliminar empleado", "Cerrar sesión forzada").
- **`btn-lg` / `btn-xl`:** móvil y landing donde el dedo necesita 44px+. **`btn-sm`:** dentro de filas de tabla con poco espacio vertical.
- **`btn-icon`:** controles compactos con un solo icono (notificaciones, flechas de navegación, editar).

### Cuándo NO usar

- No uses dos `.btn-primary` en la misma pantalla: compiten y confunden al usuario.
- No uses `.btn-danger` para acciones reversibles; es rojo porque no hay vuelta atrás.
- No uses `.btn-xl` dentro del dashboard: es de landing. La escala marketing no entra en la app.
- No anides botones dentro de botones. Si necesitas jerarquía, usa `.btn-sm` dentro de un `.btn-lg` contextual.
- No uses `.btn-block` en desktop sin necesidad: el ancho completo en un monitor de 1440px produce un botón ridículamente largo.

### Ejemplo HTML

```html
<!-- Primaria -->
<button class="btn btn-primary">
  <svg width="15" height="15" ...><path d="M12 5v14M5 12h14"/></svg>
  Añadir empleado
</button>

<!-- Secundaria -->
<button class="btn btn-secondary">Exportar</button>

<!-- Ghost con icono -->
<button class="btn btn-ghost btn-icon" aria-label="Actualizar">
  <svg width="15" height="15" ...>...</svg>
</button>

<!-- Loading -->
<button class="btn btn-primary" data-state="loading">
  <span class="spinner" aria-hidden="true"></span>
  <span class="btn-label">Guardando…</span>
</button>

<!-- Tamaño grande (móvil/kiosco) -->
<button class="btn btn-primary btn-lg btn-block">Fichar entrada</button>
```

---

## 2. Inputs y formularios

**Clases base:** `.field` (contenedor), `.input` (campo), soporte para todos los `<input>` nativos, `<select>`, `<textarea>`.

Los inputs usan `--bg-app` en reposo para distinguirse de la tarjeta blanca que los contiene, y pasan a blanco con ring al enfocar.

### Variaciones

| Elemento | Clase / selector | Comportamiento |
|---|---|---|
| Contenedor de campo | `.field` | Flex column, gap 4px, label en mayúsculas |
| Fila de dos campos | `.field-row` | Grid de dos columnas |
| Input texto/email/... | `.input` o `input[type=*]` | Estilizado automáticamente |
| Select | `select` | Apariencia nativa oculta, flecha SVG inline |
| Textarea | `textarea` | min-height 84px, `resize: vertical` |
| Switch | `.switch` + `.switch-track` | Toggle 44×26px |
| Pista contextual | `.field-hint` | Texto secundario bajo el campo |
| Error | `.field-error` | Rojo, min-height para reservar espacio |
| Estado error campo | `.input[aria-invalid="true"]` | Ring rojo + borde danger |
| Estado éxito campo | `.input.is-success` | Borde verde |

### Cuándo usar

- **`.field`:** siempre que un input tenga label. Garantiza espaciado y label en mayúsculas con `--tracking-label`.
- **`.field-row`:** dos campos relacionados en paralelo (CIF + teléfono, fecha desde + hasta).
- **`.switch`:** configuración binaria de preferencias (notificaciones, modo offline NFC). Nunca para filtros.
- **`.field-error`:** validación tras envío. Reserva `min-height: 1.25em` para que la fila no salte al aparecer el error.
- **`.field-hint`:** ayuda contextual permanente ("Para empleados sin tarjeta NFC asignada").

### Cuándo NO usar

- No uses `.switch` para filtros de tabla: usa un `<select>` o checkboxes. El switch es de preferencias persistentes.
- No uses `.input.is-success` para "todo correcto": el éxito de un campo se comunica con el badge o el submit, no con el borde. Resérvalo para validación en vivo (DNI válido, email disponible).
- No pongas el mensaje de error como código crudo ("ERR_401"): el sistema es humano, traduce.
- No uses `textarea` con `resize: none`: el usuario necesita ajustar la altura en textos largos.

### Ejemplo HTML

```html
<div class="field">
  <label for="cfg-nombre">Nombre</label>
  <input type="text" id="cfg-nombre" class="input" value="Restaurante La Marina">
</div>

<div class="field-row">
  <div class="field">
    <label for="cfg-cif">CIF</label>
    <input type="text" id="cfg-cif" class="input" value="B12345678">
  </div>
  <div class="field">
    <label for="cfg-tel">Teléfono</label>
    <input type="tel" id="cfg-tel" class="input">
  </div>
</div>

<!-- Con error -->
<div class="field">
  <label for="email">Correo</label>
  <input type="email" id="email" class="input" aria-invalid="true">
  <span class="field-error">Introduce un correo válido.</span>
</div>

<!-- Con pista -->
<div class="field">
  <label for="pin">PIN de respaldo</label>
  <input type="text" id="pin" class="input" placeholder="4 dígitos">
  <span class="field-hint">Para empleados sin tarjeta NFC asignada.</span>
</div>

<!-- Switch -->
<label class="switch">
  <input type="checkbox" checked>
  <span class="switch-track"></span>
  <span class="sr-only">Fichaje NFC</span>
</label>

<!-- Select -->
<select aria-label="Turno">
  <option value="">Todos los turnos</option>
  <option>Mañana</option>
  <option>Tarde</option>
</select>
```

---

## 3. Cards (superficies)

**Clase base:** `.card`

La superficie fundamental del dashboard. Fondo blanco, radio 10px, sombra hairline sutil que se eleva al hover.

### Variaciones

| Clase | Padding | Uso |
|---|---|---|
| `.card` | — | Base, sin padding |
| `.card-pad` | 20px | Tarjeta estándar (gráficos, listas) |
| `.card-pad-lg` | 28px | Tarjeta destacada |
| `.card--flat` | — | Sin elevación al hover |
| `.card-header` | 16px | Cabecera con título + acción |
| `.card-body` | 16px | Cuerpo |
| `.card-footer` | 16px | Pie con borde superior |
| `.divider` | — | Separador horizontal de 1px |

### Cuándo usar

- **`.card`:** contenedor de cualquier bloque de contenido en el dashboard (KPIs, gráficos, listas, tablas).
- **`.card-header` + `.card-body`:** cuando la tarjeta tiene título y contenido (ver Ubicación: "Últimos fichajes", "Fichajes por hora").
- **`.card--flat`:** tarjetas anidadas dentro de otra tarjeta o en contextos donde el hover sería ruidoso.
- **`.divider`:** separar secciones dentro de un panel sin crear una tarjeta nueva.

### Cuándo NO usar

- No uses `.card` para cada elemento de una lista: usa `ul` + estilos de item. Una tarjeta por elemento produce ruido visual.
- No anides `.card` dentro de `.card` sin `.card--flat`: la sombra duplicada confunde la jerarquía.
- No uses `.card-pad-lg` dentro del dashboard sin motivo: es para superficies destacadas, no para todo.

### Ejemplo HTML

```html
<article class="card card-pad">
  <div class="card-header">
    <h3>Fichajes por hora</h3>
  </div>
  <div class="card-body">
    <div class="chart-container" data-chart="fichajes-hora">
      <svg viewBox="0 0 600 240" role="img" aria-label="Gráfico de barras">
        <g class="chart-bars"></g>
      </svg>
    </div>
  </div>
</article>

<!-- Con cabecera y pie -->
<article class="card">
  <div class="card-header"><h3>Resumen</h3></div>
  <div class="card-body">Contenido…</div>
  <div class="card-footer">
    <button class="btn btn-secondary btn-sm">Ver detalle</button>
  </div>
</article>
```

---

## 4. Tablas

**Selectores:** `table`, `thead th`, `tbody td`, `.table-scroll`, `.cell-num`, `.cell-actions`

Densidad alta pero legible: padding 12×16px. El gerente quiere ver todo su equipo de un vistazo, no una tarjeta por empleado.

### Variaciones

| Clase / selector | Uso |
|---|---|
| `table` base | `width: 100%`, `border-collapse: collapse` |
| `thead th` | Label mayúsculas, color secundario, borde inferior |
| `tbody td` | Caption 13px, borde hairline, hover sutil |
| `.table-scroll` | Wrapper para scroll horizontal en móvil (`min-width: 620px` en la tabla interior) |
| `.cell-num` | Alineación derecha + `tabular-nums` |
| `.cell-actions` | Alineación derecha, `white-space: nowrap` |
| `.tabular` (en celdas) | Cifras que no bailan al actualizarse |

### Cuándo usar

- **Tabla:** cuando el gerente necesita comparar filas de un vistazo (lista de empleados, registro de fichajes, resumen por empleado). La densidad es una característica, no un defecto.
- **`.table-scroll`:** siempre que la tabla pueda tener más de 5 columnas en móvil. El wrapper garantiza scroll táctil sin romper el layout.
- **`.cell-num` + `.tabular`:** columnas de horas, DNIs, fechas. Los números alineados a la derecha se comparan mejor; `tabular-nums` evita que el layout salte al cambiar un "1" por un "0".
- **`.cell-actions`:** columna final con botones de acción por fila.

### Cuándo NO usar

- No uses tabla para mostrar un solo registro: usa una tarjeta de detalle.
- No uses tabla en móvil con más de 6 columnas sin `.table-scroll`: el zoom manual es hostil.
- No uses `.cell-num` en columnas de texto (nombres, descripciones): rompe la lectura izquierda-a-derecha.
- No pongas badges de estado en la columna de acciones; el estado es información, va en su propia columna.

### Ejemplo HTML

```html
<div class="table-scroll">
  <table>
    <thead>
      <tr>
        <th scope="col">Nombre</th>
        <th scope="col">Turno</th>
        <th scope="col">Estado</th>
        <th scope="col">Último fichaje</th>
        <th scope="col"><span class="sr-only">Acciones</span></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Jordi Alba</td>
        <td>Mañana</td>
        <td><span class="badge badge-active">Activo</span></td>
        <td class="tabular">Hoy 08:02</td>
        <td class="cell-actions">
          <button class="btn btn-ghost btn-icon" aria-label="Editar Jordi Alba">
            <svg ...>...</svg>
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## 5. Badges de estado

**Clase base:** `.badge`

Un badge = un estado. Nunca texto libre. La pastilla (`.badge--pill`) se usa para presencia en vivo; el rectángulo para estados de fila en tabla, donde la pastilla compite con el texto.

### Variaciones de estado

| Clase | Color | Significado |
|---|---|---|
| `.badge-ok` / `.badge-active` / `.badge-approved` | Verde (success-tint) | Correcto, activo, aprobado |
| `.badge-late` | Naranja (brand-tint-12) | Retraso, overtime alto |
| `.badge-incident` / `.badge-rejected` | Rojo (danger-tint) | Incidencia, rechazado |
| `.badge-inactive` | Gris (rgba 0.06) | Inactivo, no prioritario |
| `.badge-pending` | Ámbar (warning-tint) | Pendiente de revisión |
| `.badge-on-leave` | Azul (info-tint) | De baja |
| `.badge-syncing` | Ámbar + dot pulsante | Sincronizando / en cola |

**Variaciones de forma:**

| Clase | Forma | Uso |
|---|---|---|
| `.badge` | Rectángulo (radius-xs 4px) | Estados de fila en tabla |
| `.badge--pill` | Pastilla (radius-pill) | Presencia en vivo, navbar |

**Indicador de conexión:** `.presence` (pastilla verde "online") y `.presence.is-offline` (gris). Va en la navbar.

### Cuándo usar

- **Rectángulo (`.badge`):** estados en filas de tabla (Activo, Correcto, Pendiente, Incidencia). El rectángulo no compite con el texto adyacente.
- **Pastilla (`.badge--pill`):** presencia en vivo en la navbar ("En línea"), estados flotantes fuera de tabla.
- **`.badge-syncing`:** fichajes pendientes de sincronizar. Es warning, nunca danger: no sincronizado todavía no es un error, es transitorio.
- **`.badge-late`:** retraso en fichaje u overtime alto. Naranja de marca, no rojo: no es un error, es una alerta.
- **`.presence`:** indicador de conexión en la navbar.

### Cuándo NO usar

- No uses un badge para texto libre o decoración: un badge comunica un estado definido.
- No uses `.badge-incident` para algo recuperable: el rojo significa error real.
- No uses `.badge--pill` dentro de una tabla: la curvatura compite con el texto de la celda. Usa el rectángulo.
- No inventes colores fuera de la paleta: cada estado ya tiene su tint asignado.

### Ejemplo HTML

```html
<!-- Estado en tabla -->
<td><span class="badge badge-active">Activo</span></td>
<td><span class="badge badge-pending">Pendiente</span></td>
<td><span class="badge badge-incident">Incidencia</span></td>

<!-- Sincronizando -->
<span class="badge badge-syncing"><span class="dot"></span> Sincronizando</span>

<!-- Presencia en navbar -->
<span class="presence"><span class="dot"></span> En línea</span>

<!-- Pastilla de presencia -->
<span class="badge badge-ok badge--pill">En línea</span>
```

---

## 6. Modales

**Clase base:** `.modal-overlay` (scrim + centrado) → `.modal` (caja)

Overlay con scrim 25% negro + blur 4px. La caja sube con `tu-rise` (200ms). Cabecera y pie son sticky para contenido largo.

### Variaciones

| Clase | Uso |
|---|---|
| `.modal-overlay` | Scrim fijo, centra contenido, padding 20px |
| `.modal` | Caja base: max-width 500px, max-height 85vh, scroll vertical |
| `.modal-wide` | max-width 620px (formularios largos, confirmación con detalle) |
| `.modal-header` | Sticky top, título + cierre |
| `.modal-body` | Padding 20px, contenido scrollable |
| `.modal-footer` | Sticky bottom, acciones alineadas a la derecha |
| `.modal-close` | Botón icono 32px, hover gris |

### Cuándo usar

- **Modal:** confirmación de acción destructiva ("¿Eliminar empleado?"), edición de un registro sin abandonar la página, formularios cortos de alta/baja.
- **`.modal-wide`:** cuando el formulario tiene más de 6 campos o necesita una columna de contexto.
- **Cabecera sticky:** cuando el body puede crecer y necesita scroll, el título siempre visible.
- **Pie sticky:** las acciones de confirmación siempre accesibles sin hacer scroll hasta el final.

### Cuándo NO usar

- No uses modal para advertencias pasajeras: eso es un toast.
- No uses modal para editar campos de una fila: usa edición inline o una tarjeta de detalle.
- No uses `.modal-wide` para un simple "¿Estás seguro?": el ancho excesivo vacío se ve mal.
- No anides modales. Si necesitas un segundo nivel, cierra el primero.
- No uses modal en móvil para contenido largo: el 85vh con scroll dentro de scroll es hostil. Considera una página completa.

### Ejemplo HTML

```html
<div class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="m-title">
  <div class="modal">
    <div class="modal-header">
      <h3 id="m-title">Eliminar empleado</h3>
      <button class="modal-close" aria-label="Cerrar">
        <svg width="18" height="18" ...><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <div class="modal-body">
      <p>¿Seguro que quieres eliminar a <strong>Marta Ruiz</strong>?
         Esta acción no se puede deshacer.</p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost">Cancelar</button>
      <button class="btn btn-danger">Eliminar</button>
    </div>
  </div>
</div>
```

---

## 7. Toasts

**Clase base:** `.toast-container` (contenedor fijo) → `.toast` (ítem)

Notificaciones no intrusivas que aparecen arriba a la derecha, se deslizan entrando (`tu-slide-in`) y saliendo (`toast-out`). El contenedor es `pointer-events: none` para no bloquear clicks; cada toast es `pointer-events: auto`.

### Variaciones

| Clase | Fondo | Uso |
|---|---|---|
| `.toast-success` | Verde (success-strong) | Operación completada |
| `.toast-error` | Rojo (danger) | Error real, acción fallida |
| `.toast-warning` | Ámbar (warning-strong) | Advertencia no bloqueante |
| `.toast-info` | Azul (info) | Información neutra |
| `.toast-out` | — | Animación de salida (`tu-slide-out` forwards) |

**Contenedor:** `.toast-container` — `position: fixed; top: 20px; right: 20px; z-index: 200; max-width: 340px`.

### Cuándo usar

- **Success:** "Fichaje registrado", "Cambios guardados", "Empleado añadido". Confirmación de que algo fue bien.
- **Error:** "No se pudo sincronizar", "PIN incorrecto". El usuario necesita saber pero no necesita decidir.
- **Warning:** "Modo offline activado", "Sesión expira en 5 min". Advertencia no bloqueante.
- **Info:** "Nueva versión disponible". Neutral.

### Cuándo NO usar

- No uses toast para errores que requieren decisión: eso es un modal.
- No uses toast para información que el usuario necesita consultar después: los toasts desaparecen. Usa un banner persistente o un registro.
- No acumules más de 3 toasts simultáneos: el contenedor se vuelve ruido. Si hay muchos, agrupa.
- No uses `.toast-error` para validación de formulario: el error va en el campo (`.field-error`), no flotando.

### Ejemplo HTML

```html
<div class="toast-container" aria-live="polite" aria-atomic="false">
  <div class="toast toast-success">
    <svg width="16" height="16" ...>...</svg>
    Fichaje registrado (08:02)
  </div>
  <div class="toast toast-error">
    <svg width="16" height="16" ...>...</svg>
    No se pudo sincronizar. Reintentando…
  </div>
  <div class="toast toast-warning toast-out">
    Modo offline activado
  </div>
</div>
```

---

## 8. Navegación

Tres patrones de navegación definidos en el sistema.

### 8.1 Items de sidebar — `.nav-item`

Items de la navegación lateral del dashboard. Altura táctil 44px, radio 6px, color secundario en reposo, naranja tint 8% + texto naranja cuando está activo.

| Clase | Estado |
|---|---|
| `.nav-item` | Reposo: gris secundario |
| `.nav-item:hover` | Fondo `--bg-hover`, texto primario |
| `.nav-item.active` | Fondo `--brand-tint-08`, texto `--brand`, peso 500 |

```html
<div class="nav-item active" data-page="dashboard" role="button" tabindex="0">
  <svg width="18" height="18" ...>...</svg>
  <span class="nav-label">Dashboard</span>
</div>
```

### 8.2 Tabs — `.tabs` + `.tab`

Pestañas horizontales para secciones de configuración. Borde inferior 2px transparente, se vuelve naranja al activar (`margin-bottom: -1px` para empalmar con el borde del contenedor).

| Clase | Estado |
|---|---|
| `.tabs` | Contenedor flex con scroll horizontal |
| `.tab` | Reposo: gris, borde transparente |
| `.tab:hover` | Texto primario |
| `.tab.active` | Texto naranja, borde inferior naranja, peso 500 |
| `.tab-panel` | Oculto por defecto |
| `.tab-panel.active` | Visible |

```html
<div class="tabs" role="tablist">
  <button class="tab active" role="tab" aria-selected="true" data-tab="empresa">Empresa</button>
  <button class="tab" role="tab" aria-selected="false" data-tab="nfc">NFC</button>
  <button class="tab" role="tab" aria-selected="false" data-tab="notif">Notificaciones</button>
</div>
<section class="tab-panel active" role="tabpanel" data-panel="empresa">
  Contenido…
</section>
```

### 8.3 Control segmentado — `.segmented`

Selector entre opciones mutuamente excluyentes (idioma, vista compacta/Lista). Pastilla con fondo gris, el segmento activo se eleva con sombra hairline y texto naranja.

```html
<div class="segmented" role="group" aria-label="Idioma">
  <button class="active">ES</button>
  <button>CA</button>
  <button>EN</button>
</div>
```

### Cuándo usar / no usar

- **`.nav-item`:** navegación principal del sidebar. Una sola sección activa.
- **`.tabs`:** secciones dentro de una misma página (Ajustes: Empresa / NFC / Notificaciones).
- **`.segmented`:** cambiar de vista o idioma entre 2-4 opciones. Si hay más, usa un `<select>`.
- No uses `.tabs` para navegación entre páginas distintas: rompe el back del navegador. Usa `.nav-item` o enlaces.
- No uses `.segmented` para filtros de tabla: el select nativo es más claro y soporta muchas opciones.

---

## 9. Skeletons y carga

**Clase base:** `.skeleton`

En pantallas de datos el skeleton comunica la forma de lo que viene; el spinner solo comunica espera. El spinner sobrevive únicamente dentro de botones, donde no hay forma que anticipar.

### Variaciones de skeleton

| Clase | Uso |
|---|---|
| `.skeleton` | Base: fondo gris 4%, shimmer animado, texto transparente |
| `.skeleton-text` | Línea de texto: `height: 0.75em` |
| `.skeleton-line` | Línea de bloque: `height: 12px` |
| `.skeleton-w-40` | Ancho 40% |
| `.skeleton-w-60` | Ancho 60% |
| `.skeleton-w-80` | Ancho 80% |

### Spinner

`.spinner` — 16px, borde 2px, gira a 0.6s. Color `currentColor` para heredar el contexto. Va dentro de botones con `data-state="loading"`.

### Cuándo usar

- **Skeleton:** al cargar una vista con contenido estructurado (tabla, lista, tarjeta de KPI). El usuario ve la forma antes que el contenido y no salta el layout.
- **Skeleton con `.skeleton-w-*`:** imita el ancho real del contenido (título ~80%, línea secundaria ~60%, metadata ~40%).
- **Spinner dentro de botón:** el botón guarda su ancho y muestra espera sin perder forma.

### Cuándo NO usar

- No uses spinner para cargar una vista completa: no anticipa la forma y parece estático.
- No uses skeleton para esperas < 200ms: el parpadeo es peor que la espera.
- No uses spinner fuera de un botón en el dashboard: la regla del sistema es skeleton para datos.
- Respeta `prefers-reduced-motion`: el CSS ya desactiva el shimmer, pero no añadas loaders adicionales que lo ignoren.

### Ejemplo HTML

```html
<!-- Skeleton de una tarjeta -->
<article class="card card-pad">
  <div class="card-header">
    <h3 class="skeleton skeleton-w-60">.</h3>
  </div>
  <div class="card-body">
    <span class="skeleton skeleton-line skeleton-w-80"></span>
    <span class="skeleton skeleton-line skeleton-w-60"></span>
    <span class="skeleton skeleton-line skeleton-w-40"></span>
  </div>
</article>

<!-- Skeleton de tabla -->
<table>
  <tbody>
    <tr>
      <td><span class="skeleton skeleton-text skeleton-w-80">.</span></td>
      <td><span class="skeleton skeleton-text skeleton-w-40">.</span></td>
      <td><span class="skeleton skeleton-text skeleton-w-60">.</span></td>
    </tr>
  </tbody>
</table>

<!-- Spinner en botón -->
<button class="btn btn-primary" data-state="loading">
  <span class="spinner" aria-hidden="true"></span>
  <span class="btn-label">Guardando…</span>
</button>
```

---

## 10. Estado vacío

**Clase base:** `.empty-state`

Patrón definido en el documento de visión: una tabla o panel nunca se queda simplemente en blanco.

| Clase | Uso |
|---|---|
| `.empty-state` | Contenedor centrado, padding 48×24, gap 12px |
| `.empty-state-icon` | Icono 48px, color `--text-quaternary` (15%) |
| `.empty-state h4` | Título, peso 600 |
| `.empty-state p` | Descripción, color secundario, max 42ch |
| `.empty-state .btn` | CTA opcional |

### Cuándo usar / no usar

- **Usa:** cuando una tabla, lista o panel no tiene datos (sin empleados, sin fichajes hoy, sin incidencias).
- **No uses** un mensaje genérico "No hay datos": el estado vacío debe explicar qué falta y cómo solucionarlo ("Añade tu primer empleado para empezar a fichar").
- **No uses** el estado vacío como página de error: es para ausencia legítima de contenido, no para fallos.

```html
<div class="empty-state">
  <div class="empty-state-icon">
    <svg width="48" height="48" ...><use href="#i-empty-people"/></svg>
  </div>
  <h4>Sin incidencias</h4>
  <p>Cuando un fichaje llegue con retraso o error, aparecerá aquí para que lo revises.</p>
</div>
```

---

## 11. Banners

**Clase base:** `.banner`

Barras de ancho completo para comunicar estado del sistema (demo, offline). Aparecen en la parte superior, no son descartables.

| Clase | Fondo | Uso |
|---|---|---|
| `.banner-demo` | Ámbar (warning) + texto blanco | Entorno de demostración |
| `.banner-offline` | Ámbar tint + texto strong | Sin conexión, datos locales |

### Cuándo usar / no usar

- **`.banner-demo`:** visible en el entorno de prueba para que nadie confunda datos reales.
- **`.banner-offline`:** modo offline activado, los fichajes se guardan localmente.
- **No uses** banner para promociones o marketing dentro del dashboard: es un espacio de estado, no de venta.

```html
<div class="banner banner-offline" role="status">
  <svg width="14" height="14" ...>...</svg>
  Sin conexión. Los fichajes se guardan localmente y se sincronizarán al recuperar la red.
</div>
```

---

## 12. Tipografía utilitaria

Clases de texto para aplicar escala y color sin inventar estilos.

### Escala de texto

| Clase | Tamaño | Peso |
|---|---|---|
| `.t-display` | 34px | 600 |
| `.t-h1` | 22px | 600 |
| `.t-h2` | 18px | 600 |
| `.t-body` | 15px | 400 |
| `.t-body-sm` | 14px | 400 |
| `.t-caption` | 13px | 500 |
| `.t-micro` | 11px mono | 500 |
| `.t-label` | 11px mayúsculas | 600 |

### Colores utilitarios

`.t-muted` (secundario), `.t-faint` (terciario), `.t-brand` (naranja), `.t-danger`, `.t-success`, `.t-warning`.

### Regla de oro

No uses la escala de marketing (`.t-hero`, `.t-section`, `.t-lead` — definida con `clamp()`) dentro del dashboard. Esos tokens viven separados para que nadie los use en la app. La app tiene su propia escala, más pequeña y densa.

```html
<h1 class="t-h1">Dashboard</h1>
<p class="t-body-sm t-muted">Sábado, 8 de agosto de 2026</p>
<span class="t-label">Empleados activos</span>
<span class="t-micro t-faint">v2.1.0</span>
```

---

## Apéndice: tokens de layout y z-index

Para referencia rápida al ensamblar componentes compuestos.

| Token | Valor | Uso |
|---|---|---|
| `--sidebar-w` | 224px | Ancho sidebar expandido |
| `--sidebar-rail-w` | 60px | Sidebar colapsado (icono only) |
| `--navbar-h` | 56px | Altura de la barra superior |
| `--container` | 1100px | Ancho máximo de contenido |
| `--measure` | 68ch | Ancho máximo de párrafo |
| `--touch-min` | 44px | Target táctil mínimo (Apple HIG) |
| `--z-modal` | 100 | Modal sobre todo |
| `--z-toast` | 200 | Toast sobre modal |
| `--z-navbar` | 50 | Navbar sticky |
| `--z-sidebar` | 40 | Sidebar |

---

**Fin del documento.** Para cualquier nuevo componente, añádelo a `design_system.css` primero, luego documentalo aquí. El CSS es la fuente de verdad; esta guía es el índice legible.