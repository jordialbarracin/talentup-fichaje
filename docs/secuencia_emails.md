# Secuencia de Onboarding por Email — TalentUP Fichaje

> 5 emails automáticos, uno por día, durante la primera semana de prueba.
> Objetivo: llevar al cliente desde la cuenta vacía hasta el primer fichaje real.
> Tono: directo, útil, sin humo. Coincide con `email_ventas.md` y `email_bienvenida.md`.
> Cada email cubre un paso del onboarding (`onboarding.md`, días 1–5).

---

## Email 1 — Día 1: Bienvenida y crear la cuenta

**Asunto:** Día 1 de 5: crea tu cuenta en 10 minutos

Hola [Nombre],

Empieza hoy. Tienes 14 días de prueba y el objetivo es dejar el fichaje funcionando esta semana, no al final del verano.

Hoy solo una cosa: **crear tu cuenta**.

1. Entra en app.talentup-fichaje.com y pulsa **Crear cuenta**.
2. Rellena tu nombre, email profesional, teléfono y una contraseña de 10 caracteres.
3. Introduce el **pin de activación** de 8 dígitos que venía en la caja del kit. Así vinculamos el terminal a tu cuenta.
4. Confirma el email que te llega en 2 minutos y inicia sesión.

Si el email no aparece, revisa spam. Si el pin se rechaza, escríbeme a soporte@talentup-fichaje.com con el número de serie del lector NFC.

Mañana configuras el restaurante. 10 minutos hoy, 15 mañana.

Un saludo,

Jordi Albarracín
Fundador, TalentUP Fichaje

**[Crear cuenta →](https://app.talentup-fichaje.com)**

---

## Email 2 — Día 2: Dar de alta la empresa

**Asunto:** Día 2 de 5: da de alta tu restaurante (15 min)

Hola [Nombre],

Ayer creaste la cuenta. Hoy le damos marco legal.

Entra en **Configuración → Datos del restaurante** y completa:

- Nombre comercial, razón social y CIF
- Dirección y teléfono del local
- **Convenio colectivo** (ej. Hostelería Madrid 2024-2026). Esto define cómo se calculan las horas extras.
- **Tolerancia de fichaje**: minutos de margen antes de marcar un retraso como incidencia. Por defecto, 10.
- **Período de cálculo**: semanal, quincenal o mensual.

Guarda. El sistema valida el CIF y genera el identificador de tu establecimiento. A partir de aquí, todo queda asociado a este local.

Si tienes varios restaurantes, cada uno es un tenant independiente con su propio billing. Un Super Admin del grupo los ve todos desde una vista consolidada.

15 minutos. Mañana, la plantilla.

Un saludo,

Jordi Albarracín
TalentUP Fichaje

**[Configurar mi restaurante →](https://app.talentup-fichaje.com)**

---

## Email 3 — Día 3: Añadir empleados

**Asunto:** Día 3 de 5: carga tu plantilla (30 min o 5 con Excel)

Hola [Nombre],

Hoy metes a tu gente en el sistema.

Abre **Empleados → Nuevo empleado**. Para cada uno:

- Nombre, DNI/NIE, email y teléfono
- Puesto (sala, cocina, barra, limpieza)
- Rol: **Manager** (entra al dashboard) o **Employee** (solo ficha)
- **PIN de 4 dígitos** para fichar. El sistema sugiere uno, puedes cambiarlo
- Foto opcional, se ve en el terminal al fichar

Si tu plantilla es grande, no lo hagas a mano: **Empleados → Importar Excel/CSV**. Descargas la plantilla, la rellenas, la subes. 5 minutos para 50 personas.

Ojo: los DNI duplicados se rechazan. Si alguien tiene NIE en trámite, usa un identificador interno y lo actualizas luego.

Mañana configuras los turnos. Si ya tienes el horario de la semana en la cabeza, tardas 20 minutos.

Un saludo,

Jordi Albarracín
TalentUP Fichaje

**[Añadir empleados →](https://app.talentup-fichaje.com)**

---

## Email 4 — Día 4: Configurar turnos

**Asunto:** Día 4 de 5: define turnos y planifica la semana (20 min)

Hola [Nombre],

Hoy le dices al sistema qué se espera de cada empleado cada día. Sin esto, no hay incidencias ni horas extras que calcular.

Abre **Turnos → Nuevo turno** y crea los tuyos. Para un restaurante típico:

- **Mañana:** 08:00–16:00, pausa 30 min a las 13:00
- **Tarde:** 16:00–00:00, pausa 30 min a las 20:00
- **Noche:** 00:00–08:00, sin pausa
- **Partido:** 08:00–12:00 + 18:00–23:00

Para cada turno pon hora inicio, hora fin, pausa obligatoria y color. Luego ve a **Horarios → Calendario** y arrastra turnos a cada empleado por día. La vista semanal te lo muestra todo con colores.

Usa **Copiar semana** para replicar la plantilla a las siguientes.

Pitfall: si el convenio exige pausa y no la configuras, las horas calculadas no cuadran y el informe legal falla. Revisa el convenio antes de guardar.

Mañana, las tarjetas NFC.

Un saludo,

Jordi Albarracín
TalentUP Fichaje

**[Configurar turnos →](https://app.talentup-fichaje.com)**

---

## Email 5 — Día 5: Asignar NFC

**Asunto:** Día 5 de 5: vincula las tarjetas NFC (20 min)

Hola [Nombre],

Último paso. Hoy dejas el fichaje por aproximación listo para que tus empleados no tecleen el PIN.

Para cada empleado:

1. Abre **Empleados**, selecciona uno, ve a **Tarjeta NFC**.
2. Pulsa **Asignar tarjeta**. El lector queda en modo espera.
3. Acerca una tarjeta NFC blanca al lector ESP32. Bip y "Tarjeta leída: OK" en la tablet.
4. Repite con el resto.

Prueba: en el terminal, acerca la tarjeta de un empleado. Debe salir su nombre y foto. Si sale "Tarjeta no reconocida", vuelve a asignar.

¿Empleados sin tarjeta? El PIN sigue disponible, y puedes generar un **código QR** individual como alternativa.

Pitfall: dos tarjetas con el mismo UID. Si una falla, descártala y coge otra del kit. Cuestan 0,30 €.

Mañana haces el primer fichaje real. Ya casi estás.

Un saludo,

Jordi Albarracín
TalentUP Fichaje

**[Asignar tarjetas NFC →](https://app.talentup-fichaje.com)**

---

## Notas de uso

- Personaliza `[Nombre]` en cada envío con el nombre del propietario.
- Sustituye los enlaces de los CTA por el dominio real del dashboard en producción.
- La secuencia se envía automáticamente: día 1 al registro, días 2–5 en días consecutivos.
- Si el cliente se atasca un día, el email siguiente sigue llegando: el recordatorio empuja a recuperar el paso pendiente, no bloquea la secuencia.
- Tono: directo, útil, sin humo. Cada email tiene un único objetivo del día, tiempo estimado y un pitfall común. Coincide con `email_bienvenida.md` y `email_ventas.md`.
- Cubre los días 1–5 del `onboarding.md` (cuenta, empresa, empleados, turnos, NFC). Los días 6–7 (primer fichaje y revisión de datos) se cubren con recordatorios puntuales o soporte, no forman parte de esta secuencia.