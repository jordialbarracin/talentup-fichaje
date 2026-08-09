# Onboarding TalentUP Fichaje — Los primeros 7 días

**Versión:** 1.0 — Agosto 2026
**Producto:** TalentUP Fichaje (SaaS de fichaje para hostelería)
**Objetivo:** Llevar a un nuevo cliente desde la caja sellada al primer informe legal en 7 días.
**Cumplimiento:** RD-ley 8/2019, art. 34.9 ET — registro de jornada inmutable, conservación 4 años.

---

## Antes del día 1 — Lo que el cliente ya tiene

Antes de empezar el onboarding el cliente ha recibido el kit TalentUP:

- 1 × Tablet terminal con soporte de pared
- 1 × Lector NFC ESP32 con cable USB-C y alimentación
- 5 × Tarjetas NFC blancas (NTAG213)
- 1 × Guía rápida impresa
- 1 × Pin de activación de 8 dígitos (ej. `TAL-2026`)

El kit no requiere instalación técnica: se enchufa, se conecta al WiFi del local y funciona. El terminal también opera en modo offline y sincroniza cuando recupera conexión.

> **Ejemplo de cliente:** Restaurante La Tagliatella, 12 empleados, 3 turnos (mañana, tarde, noche). Owner: María. Manager: Carlos. Llegada del kit: lunes 20 de julio.

---

## Día 1 — Crear la cuenta

**Objetivo:** El owner crea su cuenta de usuario y deja el acceso listo para configurar el restaurante.

1. Abrir el navegador en la URL del dashboard (`https://app.talentup-fichaje.com`).
2. Pulsar **"Crear cuenta"** o **"Comenzar"**.
3. Completar los datos del propietario:
   - Nombre y apellidos
   - Email profesional (se usa para login y notificaciones)
   - Teléfono
   - Contraseña (mínimo 10 caracteres)
4. Introducir el **pin de activación** de 8 dígitos que venía en la caja. Esto valida que el kit es legítimo y lo vincula a la cuenta.
5. Confirmar el email desde el correo de verificación que llega en menos de 2 minutos.
6. Iniciar sesión con el email y la contraseña. La primera pantalla muestra el asistente de configuración.

**Resultado del día 1:** El owner tiene una cuenta activa, un tenant vacío asociado y acceso al dashboard en modo configuración. Aún no hay empresa, ni empleados, ni turnos.

**Tiempo estimado:** 10 minutos.

> **Pitfall común:** Si el email de verificación no llega, revisar spam. Si el pin de activación se rechaza, escribir a soporte con el número de serie del kit (en la base del lector NFC).

---

## Día 2 — Dar de alta la empresa

**Objetivo:** Configurar los datos del restaurante y el marco legal aplicable.

1. En el dashboard, abrir **Configuración → Datos del restaurante**.
2. Completar el formulario de empresa:
   - Nombre comercial (ej. "La Tagliatella")
   - Razón social y CIF
   - Dirección del establecimiento
   - Teléfono del local
   - Convenio colectivo aplicable (ej. "Hostelería Madrid 2024-2026")
3. Configurar la **tolerancia de fichaje**: minutos de margen permitidos antes de considerar un retraso como incidencia. Valor por defecto: 10 minutos.
4. Indicar el **período de cálculo**: semanal, quincenal o mensual. Esto define cómo se agrupan las horas en los informes.
5. Guardar. El sistema valida el CIF y genera el identificador de tenant (aislamiento de datos por establecimiento).

**Resultado del día 2:** El restaurante existe en el sistema con su marco legal y reglas de cálculo. A partir de aquí, todo lo que se configure queda asociado a este establecimiento.

**Tiempo estimado:** 15 minutos.

> **Multi-tenant:** Si el cliente es un grupo con varios locales (ej. Grupo RAS), cada local se da de alta como un tenant independiente con su propio billing. Un Super Admin del grupo puede ver todos los tenants desde una vista consolidada.

---

## Día 3 — Añadir empleados

**Objetivo:** Cargar la plantilla del restaurante en el sistema.

1. Abrir **Empleados → Nuevo empleado**.
2. Para cada empleado completar:
   - Nombre y apellidos
   - DNI / NIE
   - Email (opcional, para notificaciones de vacaciones)
   - Teléfono
   - Puesto (sala, cocina, barra, limpieza)
   - Rol en TalentUP: Manager o Employee
   - PIN de fichaje de 4 dígitos (el sistema sugiere uno aleatorio, se puede cambiar)
   - Foto (opcional, se muestra en el terminal al fichar)
3. Repetir para los 12 empleados del ejemplo. El dashboard permite **importar desde Excel/CSV** si la plantilla es grande: descargar la plantilla, rellenar y subir.
4. Asignar a cada Manager su turno habitual. Los Employee no necesitan turno asignado todavía (se hace el día 4).

**Resultado del día 3:** Los 12 empleados están en el sistema, cada uno con su PIN y su rol. Los managers pueden entrar al dashboard con sus credenciales; los empleados solo fichan desde el terminal.

**Tiempo estimado:** 30 minutos (12 empleados a mano) o 5 minutos con importación CSV.

> **Pitfall común:** Los DNI duplicados se rechazan. Si un empleado tiene NIE en trámite, usar un identificador interno temporal y actualizarlo cuando llegue.

---

## Día 4 — Configurar turnos

**Objetivo:** Definir los turnos del restaurante y empezar a planificar la semana.

1. Abrir **Turnos → Nuevo turno**.
2. Crear los turnos del restaurante. Para La Tagliatella:
   - **Mañana:** 08:00 — 16:00 (con pausa de 30 min a las 13:00)
   - **Tarde:** 16:00 — 00:00 (con pausa de 30 min a las 20:00)
   - **Noche:** 00:00 — 08:00 (sin pausa, 2 personas)
   - **Partido:** 08:00 — 12:00 + 18:00 — 23:00 (para jornadas divididas)
3. Para cada turno definir:
   - Hora de inicio y fin
   - Pausa obligatoria (sí/no, duración)
   - Color del turno en el calendario (mañana verde, tarde naranja, noche morado)
   - Tolerancia de entrada (minutos)
4. Abrir **Horarios → Calendario** y arrastrar turnos a cada empleado por día. La vista semanal muestra todos los turnos asignados con colores.
5. Replicar la plantilla de la primera semana a las siguientes con el botón **Copiar semana**.

**Resultado del día 4:** Los 3 turnos están configurados y la semana está planificada. El sistema sabe qué se espera de cada empleado cada día y generará incidencias si alguien ficha fuera de su turno.

**Tiempo estimado:** 20 minutos.

> **Pitfall común:** Olvidar la pausa obligatoria. Si el convenio exige pausa y no se configura, las horas calculadas serán incorrectas y el informe legal no cuadrará.

---

## Día 5 — Asignar NFC

**Objetivo:** Vincular cada tarjeta NFC a un empleado para que el fichaje sea por aproximación, sin teclear el PIN.

1. Abrir **Empleados** y seleccionar un empleado.
2. En la ficha del empleado, ir a la sección **Tarjeta NFC**.
3. Pulsar **"Asignar tarjeta"**. El sistema pone el lector NFC en modo espera.
4. Aproximar una tarjeta NFC blanca al lector ESP32. El lector emite un bip y la tablet muestra "Tarjeta leída: OK".
5. El sistema guarda el UID de la tarjeta asociado al empleado. Repetir para cada empleado.
6. Probar la asignación: en el terminal, aproximar la tarjeta de un empleado. Debe aparecer su nombre y foto. Si aparece "Tarjeta no reconocida", volver a asignar.
7. Para empleados sin tarjeta, el fichaje por **PIN** sigue disponible. También se puede generar un **código QR** individual por empleado como alternativa.

**Resultado del día 5:** Cada empleado tiene su tarjeta NFC. El terminal reconoce al empleado al aproximarse, muestra su nombre y foto, y ofrece los botones ENTRAR, SALIR, PAUSA INICIO y PAUSA FIN.

**Tiempo estimado:** 20 minutos (12 empleados).

> **Pitfall común:** Dos tarjetas con el mismo UID. Si una tarjeta falla, descartarla y usar otra del kit. Las tarjetas son NTAG213, reemplazables por 0,30 €/ud.

---

## Día 6 — Primer fichaje

**Objetivo:** Hacer el primer fichaje real y verificar que el flujo completo funciona.

1. Encender el terminal y esperar a que muestre "Terminal listo. Aproxime tarjeta o escanee QR."
2. Pedir a un empleado que aproxime su tarjeta NFC.
3. El terminal muestra:
   - Nombre del empleado y foto
   - Hora actual grande
   - Botones: **ENTRAR | SALIR | PAUSA INICIO | PAUSA FIN**
4. El empleado pulsa **ENTRAR**. El terminal confirma con un bip OK y un mensaje verde "Fichaje registrado: 08:02 — Entrada".
5. Verificar en el dashboard → **Fichajes** que el registro aparece con:
   - Empleado, fecha, hora, tipo (entrada)
   - Estado: "Dentro de turno" o "Incidencia" si llegó fuera de su turno configurado
6. Repetir con 2-3 empleados más, cubriendo entrada, pausa inicio, pausa fin y salida.
7. Probar el modo offline: desconectar el WiFi del terminal, hacer un fichaje, reconectar y comprobar que el registro se sincroniza y aparece en el dashboard.

**Resultado del día 6:** El flujo de fichaje funciona de extremo a extremo: tarjeta → terminal → sincronización → dashboard. Los registros son inmutables (no se pueden editar, solo anular con motivo y log de auditoría).

**Tiempo estimado:** 15 minutos.

> **Pitfall común:** Si el fichaje no aparece en el dashboard, comprobar que el terminal tiene conexión y que el empleado está asignado al tenant correcto. El log de sincronización del terminal muestra el estado de cada registro.

---

## Día 7 — Revisar datos

**Objetivo:** Verificar que los datos del primer día son correctos y generar el primer informe legal.

1. Abrir **Informes → Horas trabajadas**.
2. Seleccionar el período del primer día de fichajes. El informe muestra:
   - Horas trabajadas por empleado
   - Horas extras calculadas según el convenio
   - Pausas realizadas vs. obligatorias
   - Incidencias: no fichó, fichó tarde, fichó fuera de turno
3. Revisar las **incidencias** del día. Para cada incidencia:
   - Si es un error de configuración (turno mal asignado), corregir el turno y recalcular.
   - Si es un fichaje real (empleado llegó tarde), anotar el motivo en el campo de observaciones.
4. Abrir **Informes → Registro de jornada (RD-ley 8/2019)**. Este informe es el que se entregaría a una inspección de trabajo:
   - Fecha, hora inicio, hora fin, ID empleado, tipo de fichaje
   - Formato exportable en PDF con firma digital del registro
   - Conservación 4 años, registro inmutable
5. Exportar el informe en PDF y guardarlo. Verificar que abre correctamente y contiene todos los campos legales.
6. Revisar la **configuración general** una última vez: datos del restaurante, convenio, tolerancia, período de cálculo. Cualquier cambio aquí recalcula los informes.
7. Confirmar que el **billing** es correcto: en Configuración → Facturación, verificar el plan activo (Starter 29 €/mes o Pro 39 €/mes) y el establecimiento facturado.

**Resultado del día 7:** El cliente tiene su primer informe legal exportable, las incidencias revisadas y la configuración validada. El onboarding termina con el sistema operativo y cumpliendo la normativa.

**Tiempo estimado:** 30 minutos.

> **Pitfall común:** No exportar el informe del primer día. Aunque los datos están en el sistema, conviene guardar el PDF del primer día como referencia y prueba de que el registro funciona desde el inicio.

---

## Resumen del onboarding

| Día | Acción | Tiempo | Resultado |
|-----|--------|--------|-----------|
| 1 | Crear cuenta | 10 min | Cuenta activa, tenant vacío |
| 2 | Dar de alta empresa | 15 min | Restaurante configurado con convenio |
| 3 | Añadir empleados | 30 min | Plantilla cargada con PINs y roles |
| 4 | Configurar turnos | 20 min | Turnos definidos y semana planificada |
| 5 | Asignar NFC | 20 min | Tarjetas vinculadas a empleados |
| 6 | Primer fichaje | 15 min | Flujo NFC → dashboard verificado |
| 7 | Revisar datos | 30 min | Primer informe legal exportado |

**Total:** 140 minutos de configuración repartidos en 7 días. Al finalizar, el cliente tiene un sistema de fichaje completo, legal y automatizado.

## Después del día 7

Una vez completado el onboarding, el cliente entra en régimen de operación normal:

- **Diario:** los empleados fichan con NFC. El owner revisa incidencias.
- **Semanal:** el manager planifica los turnos de la semana siguiente con **Copiar semana**.
- **Mensual:** el owner exporta el informe del RD-ley 8/2019 en PDF y lo archiva.
- **Trimestral:** revisión de horas extras y ajuste de plantilla si es necesario.

El soporte de TalentUP está disponible en `soporte@talentup-fichaje.com` para incidencias. Las actualizaciones del sistema son automáticas y no requieren intervención del cliente.