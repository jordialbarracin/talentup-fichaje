# Manual de Usuario — TalentUP Fichaje

**Versión:** 1.0 — Julio 2026  
**Producto:** TalentUP Fichaje (SaaS de fichaje para hostelería)  
**URLs de desarrollo:** Backend `http://localhost:8000/api` · Frontend `http://localhost:3000` · Terminal `http://localhost:3001`

---

## 1. Introducción

### ¿Qué es TalentUP Fichaje?

TalentUP Fichaje es un sistema en la nube diseñado para que restaurantes, bares, cafeterías y cualquier negocio de hostelería gestionen el fichaje de sus empleados de forma sencilla, legal y automatizada.

Permite registrar entradas y salidas mediante **NFC, QR o PIN**, planificar turnos, controlar vacaciones, registrar bajas médicas, generar informes de horas y cumplir con la normativa del Registro de Jornada (RD-ley 8/2019).

### ¿Para quién es?

- **Owners / Dueños** de restaurantes que quieren controlar horas y costes.
- **Gerentes** que planifican turnos y aprueban vacaciones.
- **Empleados** de sala, cocina, barra, limpieza y mantenimiento.
- **Departamentos de RRHH o administración** que necesitan exportar informes para nóminas o inspecciones.

### Problemas que resuelve

| Problema | Solución de TalentUP Fichaje |
|----------|------------------------------|
| Fichajes en papel o WhatsApp desordenados | Fichaje digital con NFC, QR o PIN |
| No se sabe quién llega tarde o se marcha antes | Alertas de incidencias, retrasos y ausencias |
| Planificar turnos en Excel es lento | Calendario interactivo con turnos y colores |
| Vacaciones y bajas sin control centralizado | Flujo de solicitudes y registro médico |
| Miedo a la inspección de trabajo | Informe RD-ley 8/2019 exportable en PDF/Excel |
| Dispositivos caros o difíciles de instalar | Kit hardware 49 € + suscripción desde 29 €/mes |

---

## 2. Primeros pasos

### 2.1 Recibir el kit

Tras contratar TalentUP Fichaje recibirás una caja con:

- 1 × Tablet terminal con soporte (acceso en `http://localhost:3001` en entorno local).
- 1 × Lector NFC ESP32 con cable USB-C y alimentación.
- 5 × Tarjetas NFC blancas.
- 1 × Guía rápida impresa.
- 1 × Pin de activación de 8 dígitos.

> **Ejemplo:** Restaurante La Tagliatella recibe el kit el lunes 20 de julio. El pin de activación es `TAL-2026`.

### 2.2 Enchufar el dispositivo

1. Conecta el lector NFC ESP32 a la corriente con el adaptador incluido.
2. Conecta el cable USB-C al ESP32 y a la tablet (o a un router con puerto USB de carga).
3. Enciende la tablet y abre el navegador en la URL del terminal.
4. Espera hasta que la pantalla muestre **“Terminal listo. Aproxime tarjeta o escanee QR.”**

### 2.3 Conectar al WiFi

En el menú del terminal:

1. Pulsa el icono de engranaje (⚙️) arriba a la derecha.
2. Selecciona **Red WiFi**.
3. Elige la red del restaurante, por ejemplo `LaTagliatella_Guest`.
4. Introduce la contraseña.
5. Pulsa **Conectar**. Aparecerá una ✓ verde cuando tenga internet.

> El terminal también funciona en **modo offline**: guarda los fichajes localmente y los sincroniza cuando recupera conexión.

---

## 3. Registro

### 3.1 Crear la cuenta de owner

La primera vez que se usa TalentUP Fichaje hay que crear el restaurante y el usuario propietario.

1. Abre el navegador en `http://localhost:3000`.
2. Pulsa **“Crear cuenta”** o **“Comenzar”**.
3. Completa los datos del restaurante:
   - **Nombre comercial:** Restaurante La Tagliatella
   - **Razón social:** La Tagliatella SL
   - **CIF:** B12345678
   - **Dirección:** Calle Mayor 42, Madrid
   - **Teléfono:** +34 912 345 678
   - **Email del negocio:** info@latagliatella.es
4. Completa los datos del owner:
   - **Nombre:** María García
   - **Email:** `owner@latagliatella.es`
   - **Contraseña:** `owner123`
5. Acepta las condiciones y pulsa **Crear cuenta**.

Tras unos segundos verás el mensaje **“Cuenta creada. Bienvenido a TalentUP Fichaje.”**

### 3.2 Entrar como gerente

Si ya existe la cuenta, entra directamente:

1. Ve a `http://localhost:3000`.
2. Introduce **Email:** `owner@latagliatella.es`.
3. Introduce **Contraseña:** `owner123`.
4. Pulsa **Iniciar sesión**.

> Si eres gerente sin cuenta de owner, el owner debe invitarte desde **Configuración > Usuarios** y asignarte el rol `manager`.

---

## 4. Onboarding Wizard

La primera vez que entra el owner, un asistente de 3 pasos guía la configuración inicial.

### Paso 1 — Configura tu restaurante

Se rellenan automáticamente los datos introducidos en el registro. Revisa y completa:

- **Convenio colectivo:** Hostelería
- **Comunidad autónoma:** Madrid
- **Localidad:** Madrid
- **Sector:** Restaurante
- **Tolerancia de llegada:** 5 minutos
- **Periodo de gracia:** 15 minutos
- **Días de vacaciones al año:** 30

> Para La Tagliatella se selecciona **Convenio > Hostelería** y **CCAA > Madrid**, porque el calendario laboral y los festivos se cargan automáticamente.

### Paso 2 — Crea los turnos habituales

El sistema propone 3 turnos por defecto. Puedes editarlos o añadir más:

| Turno | Horario | Color |
|-------|---------|-------|
| Mañana | 07:00 – 15:00 | `#FF6B35` (naranja) |
| Tarde | 15:00 – 23:00 | `#0F766E` (verde oscuro) |
| Noche | 23:00 – 07:00 | `#1E3A5F` (azul noche) |

Pulsa **Añadir turno** para crear los específicos del restaurante, como el turno **Partido** (10:00–23:00 con descanso 16:00–20:00) o **Rotativo**.

### Paso 3 — Añade empleados

Añade al menos un empleado de ejemplo. Para cada uno introduce:

- Nombre y apellidos
- DNI/NIE
- Número de Seguridad Social
- Teléfono y email
- Categoría profesional
- Tipo de contrato y jornada
- Turno asignado por defecto
- PIN de 4 dígitos

> **Ejemplo de empleado inicial:**
> - **Nombre:** Carlos López García
> - **DNI:** 12345678A
> - **NSS:** 28/12345678/00
> - **Teléfono:** +34 612 345 678
> - **Categoría:** COC-03
> - **Turno:** Mañana
> - **PIN:** 1234

---

## 5. Dashboard

Al iniciar sesión el owner/gerente ve el **Dashboard**, una pantalla con resumen del día y acceso a las 9 secciones.

### 5.1 Stat-cards del Dashboard

| Tarjeta | Significado | Ejemplo |
|---------|-------------|---------|
| **Fichados hoy** | Empleados que ya han registrado entrada | 4 de 10 |
| **Pendientes** | Empleados con turno asignado que aún no han fichado | 6 |
| **Incidencias** | Retrasos, ausencias o salidas anticipadas | 1 (Carlos llegó tarde) |
| **Vacaciones activas** | Días de vacaciones en curso | 21–28 jul (Carlos) |
| **Bajas activas** | Bajas médicas abiertas | 1 (Javier, IT) |
| **Horas acumuladas** | Total de horas fichadas hoy | 32 h |

### 5.2 Navegación por las 9 secciones

El menú lateral contiene estas secciones:

1. **Dashboard** — resumen del día.
2. **Empleados** — alta, baja, edición y asignación de métodos de fichaje.
3. **Calendario** — planificación visual de turnos y festivos.
4. **Turnos** — definición de turnos, colores y horarios.
5. **Fichajes** — historial de entradas/salidas e incidencias.
6. **Vacaciones** — solicitudes, aprobaciones y saldo.
7. **Bajas** — registro de bajas médicas, IT y datos de la mutua.
8. **Informes** — exportación en PDF, Excel e informe inspección.
9. **Configuración** — restaurante, convenio, calendario laboral y facturación.

---

## 6. Empleados

### 6.1 Añadir un empleado

1. Ve a **Empleados** en el menú lateral.
2. Pulsa **Nuevo empleado**.
3. Rellena los campos obligatorios:
   - Nombre: `Carlos`
   - Apellidos: `López García`
   - DNI: `12345678A`
   - NSS: `28/12345678/00`
   - Teléfono: `+34 612 345 678`
   - Email: `carlos.lopez@email.com`
   - Categoría profesional: `COC-03`
   - Tipo de contrato: `Indefinido`
   - Jornada: `Completa`
   - Horas semanales: `40`
   - Turno por defecto: `Mañana`
   - PIN: `1234`
4. Pulsa **Guardar**.

### 6.2 Editar un empleado

1. En la lista de empleados, busca a `Carlos López García`.
2. Pulsa el icono de lápiz ✏️.
3. Modifica los campos necesarios (teléfono, dirección, turno, etc.).
4. Pulsa **Guardar cambios**.

### 6.3 Asignar NFC

1. Abre la ficha del empleado.
2. Ve a la pestaña **Métodos de fichaje**.
3. Pulsa **Asignar tarjeta NFC**.
4. Acerca una tarjeta NFC al lector.
5. El campo se rellena automáticamente, por ejemplo `04:A1:B2:C3:D4:E5`.
6. Pulsa **Guardar**.

### 6.4 Generar QR

1. En la ficha del empleado, pestaña **Métodos de fichaje**.
2. Pulsa **Generar QR**.
3. Aparece un código QR único.
4. Puedes descargarlo en PNG e imprimirlo para el empleado.

### 6.5 Asignar PIN

1. En la misma pestaña, campo **PIN de 4 dígitos**.
2. Introduce el PIN, por ejemplo `1234`.
3. Pulsa **Guardar**. El sistema lo almacena de forma segura mediante hash.

### 6.6 Dar de baja

1. Abre la ficha del empleado.
2. Pulsa **Dar de baja** (arriba a la derecha).
3. Selecciona la fecha de baja y el motivo.
4. Pulsa **Confirmar**. El empleado pasa a estado **inactivo** y no puede fichar.

---

## 7. Calendario

### 7.1 Ver horarios

1. Ve a **Calendario**.
2. Arriba selecciona la semana o el mes que quieres consultar.
3. Cada día muestra los turnos asignados con su color.

> Ejemplo: la semana del 20 al 26 de julio muestra a Carlos en turno Mañana (naranja) de lunes a viernes.

### 7.2 Asignar turnos

1. Haz clic en una celda del día y del empleado.
2. Se abre un selector de turnos.
3. Elige el turno, por ejemplo **Partido** para el sábado.
4. Pulsa **Asignar**. La celda se colorea con el color del turno.

### 7.3 Ver festivos

Los festivos aparecen marcados con una bandera 🏴 en la parte superior del día. Al pasar el ratón se muestra el nombre, por ejemplo **San Isidro Labrador** el 15 de mayo.

Para La Tagliatella (Madrid) el sistema carga automáticamente:

- Festivos nacionales (Año Nuevo, Reyes, Viernes Santo, 1 de mayo, etc.)
- Festivos autonómicos de Madrid (2 de mayo, Corpus Christi)
- Festivos locales de Madrid capital (San Isidro, La Almudena)

---

## 8. Turnos

### 8.1 Crear un turno

1. Ve a **Turnos**.
2. Pulsa **Nuevo turno**.
3. Rellena:
   - **Nombre:** Noche
   - **Código:** N
   - **Tipo:** Noche
   - **Inicio:** 23:00
   - **Fin:** 07:00
   - **Descanso:** 30 min
   - **Tolerancia:** 10 min
   - **Plus nocturnidad:** 25 €/mes
   - **Plus festividad:** 25 €/mes
   - **Color:** `#1E3A5F`
4. Pulsa **Guardar**.

### 8.2 Paleta de 10 colores recomendada

| Color | Hex | Uso recomendado |
|-------|-----|-----------------|
| Naranja | `#FF6B35` | Mañana |
| Verde oscuro | `#0F766E` | Tarde |
| Azul noche | `#1E3A5F` | Noche |
| Púrpura | `#7C3AED` | Partido |
| Ámbar | `#F59E0B` | Rotativo |
| Rosa | `#EC4899` | Formación |
| Cian | `#06B6D4` | Eventos |
| Lima | `#84CC16` | Mantenimiento |
| Rojo | `#EF4444` | Festivo / especial |
| Gris | `#6B7280` | Descanso / libre |

### 8.3 Turnos rotativos

1. Crea un turno con tipo **Rotativo**.
2. Marca la casilla **Es rotativo**.
3. Define la plantilla base, por ejemplo 07:00–15:00.
4. En el calendario asigna días concretos y edita la hora si es necesario.

### 8.4 Turnos partidos

Un turno partido tiene dos franjas de trabajo con descanso largo en medio.

Ejemplo del turno **Partido** de La Tagliatella:

- Inicio: 10:00
- Fin: 23:00
- Descanso: 16:00 – 20:00 (120 min)

Al fichar, el sistema descuenta automáticamente el descanso del cálculo de horas.

### 8.5 Turno de noche

El turno **Noche** cruza la medianoche:

- Inicio: 23:00
- Fin: 07:00 del día siguiente
- Se aplica el plus de nocturnidad configurado (25 €/mes en el seed).

El sistema calcula correctamente las horas aunque la entrada y la salida sean en días diferentes.

---

## 9. Fichajes

### 9.1 Cómo fichar el empleado

El empleado puede fichar por tres métodos:

#### A) Por PIN

1. En el terminal o en la PWA, pulsa **Fichar con PIN**.
2. Introduce el DNI/NIE o el código de empleado.
3. Introduce el PIN de 4 dígitos.
4. Pulsa **Entrada** o **Salida**.

> **Ejemplo:** Carlos introduce DNI `12345678A` y PIN `1234`. El sistema responde: **“Entrada registrada: Carlos López — 07:02”**.

#### B) Por NFC

1. Acerca la tarjeta NFC al lector.
2. El terminal lee el UID, por ejemplo `04:A1:B2:C3:D4:E5`.
3. El sistema identifica a Carlos y registra la acción.

#### C) Por QR

1. En la PWA o en un móvil, pulsa **Escanear QR**.
2. Enfoca el código QR impreso del empleado.
3. El sistema registra la entrada o salida automáticamente.

### 9.2 Historial de fichajes

1. Ve a **Fichajes** en el menú lateral.
2. Filtra por empleado, fecha o tipo de incidencia.
3. Cada fila muestra: empleado, fecha, entrada, salida, horas trabajadas y estado.

> Ejemplo: Carlos el 20 de julio — Entrada 07:02, Salida 15:05, Total 7h 33m, Estado ✅ Normal.

### 9.3 Toggle auto entrada/salida

En **Configuración > Fichajes** el owner puede activar:

- **Auto-detección entrada/salida:** el sistema alterna automáticamente entre entrada y salida al fichar, sin que el empleado tenga que elegir.
- **Fichaje offline:** permite fichajes sin conexión; se sincronizan al recuperarla.

---

## 10. Vacaciones

### 10.1 Cómo solicita vacaciones el empleado

1. El empleado accede a su perfil desde la PWA o desde el portal.
2. Pulsa **Vacaciones > Nueva solicitud**.
3. Selecciona las fechas, por ejemplo del 1 al 15 de agosto.
4. Escribe el motivo: “Vacaciones familiares”.
5. Pulsa **Enviar solicitud**.

El sistema calcula automáticamente los días laborables (11 días en el ejemplo) y descuenta el saldo disponible.

### 10.2 Cómo aprueba o rechaza el gerente

1. Ve a **Vacaciones**.
2. Verás las solicitudes pendientes, por ejemplo **Ana Martínez — 1–15 ago — 11 días**.
3. Pulsa **Ver detalle**.
4. Revisa el saldo de Ana (30 días iniciales) y la cobertura del calendario.
5. Pulsa **Aprobar** o **Rechazar**.
6. Si rechazas, indica el motivo: “Falta cobertura en turno tarde”.

El empleado recibe una notificación en la app con el resultado.

---

## 11. Bajas

### 11.1 Registrar una baja por IT

1. Ve a **Bajas**.
2. Pulsa **Nueva baja**.
3. Selecciona el empleado, por ejemplo **Javier Ruiz Gómez**.
4. Indica:
   - **Tipo:** Baja por enfermedad común (EC)
   - **Fecha inicio:** 15 de junio
   - **Fecha prevista alta:** 15 de julio
   - **Centro médico:** Hospital Clínico San Carlos
   - **Médico:** Dr. Martínez
   - **Número de parte:** PART-2026-001
   - **Mutua:** FREMAP
5. Pulsa **Guardar**.

### 11.2 Datos médicos

En la ficha de la baja puedes adjuntar:

- Parte médico escaneado (PDF o imagen)
- Informe de la mutua
- Evolución de la baja y fecha real de alta

> **Nota:** Los datos médicos están marcados como información sensible. Solo el owner y los gerentes autorizados pueden verlos.

### 11.3 Mutua

El campo **Mutua** permite registrar la entidad gestora, por ejemplo FREMAP, MAPFRE o Mutua Universal. Esto facilita el seguimiento de las comunicaciones de baja y alta a la mutua.

---

## 12. Informes

### 12.1 Generar informe PDF

1. Ve a **Informes**.
2. Selecciona el tipo **Resumen de horas**.
3. Define el periodo, por ejemplo 1–31 de julio de 2026.
4. Selecciona los empleados (todos o individuales).
5. Pulsa **Generar PDF**.
6. El navegador descarga el archivo `informe_horas_julio_2026.pdf`.

El PDF incluye:

- Logo y datos del restaurante
- Tabla de empleados con horas programadas, trabajadas, extras y ausencias
- Resumen total
- Pie de página con fecha de generación

### 12.2 Generar Excel

1. En **Informes**, selecciona **Exportar Excel**.
2. Elige el periodo y los empleados.
3. Pulsa **Descargar**.
4. El archivo `informe_horas_julio_2026.xlsx` se abre en Excel o LibreOffice.

El Excel contiene hojas separadas para horas, incidencias, vacaciones y extras.

### 12.3 Informe de inspección RD-ley 8/2019

1. Ve a **Informes > Inspección**.
2. Selecciona el periodo solicitado por la inspección, por ejemplo el segundo trimestre de 2026.
3. Pulsa **Generar informe RD-ley 8/2019**.
4. El sistema crea un PDF con:
   - Datos identificativos del restaurante (CIF B12345678)
   - Listado diario de entradas y salidas de cada empleado
   - Horas totales por día y por periodo
   - Firma digital del responsable

> Este informe cumple los requisitos del Registro de Jornada establecidos en el Real Decreto-ley 8/2019.

---

## 13. Configuración

### 13.1 Datos del restaurante

Ve a **Configuración > Restaurante** para editar:

- Nombre comercial y razón social
- CIF (B12345678)
- Dirección, ciudad, provincia y código postal
- Teléfono y email
- Web
- Logo

### 13.2 Convenio colectivo

En **Configuración > Convenio**:

- Selecciona el convenio aplicable: **Hostelería**.
- El sistema carga automáticamente categorías profesionales como COC-03, SAL-03, BAR-02, etc.
- Configura porcentajes de cotización:
  - Empleado: 6,35 %
  - Empresa: 29,90 %
- IRPF por defecto: 12 %

### 13.3 Calendario laboral

En **Configuración > Calendario laboral**:

- Selecciona la Comunidad Autónoma (Madrid) y la localidad (Madrid).
- El sistema genera automáticamente los festivos nacionales, regionales y locales.
- Puedes añadir festivos propios del restaurante (puentes, cierres por vacaciones).

### 13.4 Facturación

En **Configuración > Facturación**:

- Consulta el plan contratado (Premium).
- Añade el IBAN de domiciliación.
- Descarga facturas anteriores.
- Actualiza método de pago.

> Precios del kit: 49 € de hardware + 29 €/mes (plan básico) o 39 €/mes (plan premium).

---

## 14. Terminal NFC (Tablet)

### 14.1 Uso básico

El terminal está pensado para colocarse en la entrada del almacén o del vestuario:

1. Enciende la tablet y abre el navegador en `http://localhost:3001`.
2. La pantalla muestra:
   - Hora actual
   - Botón grande **Fichar**
   - Iconos para NFC, QR y PIN
3. El empleado elige su método y ficha.

### 14.2 Modo kiosk

Para evitar que los empleados salgan de la app:

1. En Android, activa **Pantalla fija** o **Kiosk mode**.
2. Fija el navegador con la URL del terminal.
3. Desactiva botones de navegación.
4. La tablet queda bloqueada en la pantalla de fichaje.

### 14.3 Modo offline

Si el restaurante pierde internet:

1. El terminal sigue permitiendo fichajes.
2. Los datos se guardan en el almacenamiento local.
3. Cuando vuelve la conexión, se sincronizan automáticamente.
4. El gerente puede ver en **Configuración > Terminal** el estado de sincronización.

---

## 15. PWA Móvil

### 15.1 Instalar en Android

1. Abre Chrome en el móvil y visita `http://localhost:3000/mobile/` (o la URL pública del tenant).
2. Pulsa el menú de Chrome (⋮) > **Añadir a pantalla de inicio**.
3. Confirma el nombre “TalentUP Fichaje”.
4. Aparece el icono en el escritorio del móvil.

### 15.2 Instalar en iPhone

1. Abre Safari y visita la URL de la PWA.
2. Pulsa **Compartir** > **Añadir a pantalla de inicio**.
3. Confirma el nombre.
4. El icono se añade al inicio.

### 15.3 Fichar desde el móvil

1. Abre la app de TalentUP Fichaje.
2. Introduce DNI y PIN, o escanea tu QR.
3. Pulsa **Entrada** o **Salida**.
4. El sistema usa la geolocalización para confirmar que estás en el restaurante (si está activada).

---

## 16. Hardware ESP32

### 16.1 Configurar el dispositivo NFC

El lector ESP32 se comunica con el backend mediante HTTP:

1. Conecta el ESP32 a la red WiFi del restaurante.
2. Configura la URL del backend en el firmware:
   ```
   API_BASE = http://localhost:8000/api
   ```
3. Reinicia el dispositivo.
4. En el log serie aparecerá:
   ```
   WiFi connected
   TalentUP NFC terminal ready
   Waiting for card...
   ```

### 16.2 Asignar tarjetas NFC

Hay dos formas de asignar una tarjeta:

#### Desde el backend

1. Ve a **Empleados > Carlos López > Métodos de fichaje**.
2. Pulsa **Asignar tarjeta NFC**.
3. Acerca la tarjeta al lector conectado.
4. El UID se guarda, por ejemplo `04:A1:B2:C3:D4:E5`.

#### Desde el propio terminal

1. En la pantalla del terminal, pulsa el icono de engranaje.
2. Selecciona **Emparejar tarjeta**.
3. Acerca la tarjeta.
4. Selecciona el empleado al que pertenece.
5. Confirma.

### 16.3 Probar un fichaje NFC

1. Acerca la tarjeta asignada a Carlos al lector.
2. El ESP32 envía la petición al backend.
3. El backend responde:
   ```json
   {
     "status": "ok",
     "employee": "Carlos López García",
     "type": "Entrada",
     "message": "07:02"
   }
   ```
4. En el terminal se muestra: **“OK: Carlos López — Entrada 07:02”**.

---

## 17. Preguntas frecuentes

### 1. ¿Qué pasa si un empleado olvida fichar?

El gerente puede añadir manualmente la entrada/salida desde **Fichajes > Añadir fichaje manual**. El sistema marcará la incidencia como “registro manual”.

### 2. ¿Se puede fichar sin internet?

Sí. Tanto el terminal NFC como la PWA guardan los fichajes localmente y los sincronizan cuando recuperan conexión.

### 3. ¿Cuánto cuesta el kit?

El kit hardware cuesta **49 €** de una sola vez. La suscripción es **29 €/mes** (plan básico) o **39 €/mes** (plan premium).

### 4. ¿Cumple con la ley de registro de jornada?

Sí. TalentUP Fichaje genera un informe específico conforme al **RD-ley 8/2019** con todas las entradas, salidas y horas totales.

### 5. ¿Puedo usar mi propio móvil para fichar?

Sí, instalando la PWA desde el navegador. El gerente puede requerir geolocalización para validar que el fichaje se hace en el local.

### 6. ¿Qué métodos de fichaje soporta?

NFC (tarjeta o llavero), QR (código impreso o digital) y PIN (4 dígitos).

### 7. ¿Cómo se recupera la contraseña de owner?

En la pantalla de login pulsa **“¿Has olvidado tu contraseña?”** e introduce `owner@latagliatella.es`. Recibirás un enlace de recuperación.

### 8. ¿Se pueden importar empleados desde Excel?

Sí. Desde **Empleados > Importar** puedes subir un archivo Excel con las columnas: nombre, apellidos, dni, email, teléfono, turno y pin.

### 9. ¿Qué es un turno partido?

Es un turno con dos franjas separadas por un descanso largo, por ejemplo 10:00–14:00 y 19:00–23:00 con descanso de 16:00–19:00. El sistema descuenta el descanso del total de horas.

### 10. ¿Dónde puedo consultar el soporte?

Envía un email a **soporte@talentup.es** o abre un ticket desde **Configuración > Soporte**. Incluye el CIF de tu restaurante (B12345678) para agilizar la respuesta.

---

**Fin del manual**

¿Necesitas más ayuda? Contacta con soporte en soporte@talentup.es.
