# Guía de Soporte — TalentUP Fichaje

**Versión:** 1.0 — Agosto 2026
**Producto:** TalentUP Fichaje (SaaS de fichaje para hostelería)
**Cumplimiento:** RD-ley 8/2019, art. 34.9 ET — registro de jornada inmutable, conservación 4 años.

---

## 1. Propósito

Esta guía define cómo el equipo de TalentUP atiende a un cliente que reporta un problema con el sistema de fichaje. Cubre canales de contacto, tiempos de respuesta, flujo de escalado y el diagnóstico de las cuatro incidencias más frecuentes: fichaje que no registra, lector NFC que no lee, aplicación que no carga y turno mal configurado. El objetivo es cerrar tickets rápido, con criterio, y escalar solo lo que no se resuelve en primera línea.

---

## 2. Canales de soporte

TalentUP atiende por dos canales. No hay teléfono por defecto.

### 2.1 Email

- **Dirección:** `soporte@talentup-fichaje.com`
- **Uso:** incidencias con captura, logs, números de serie o pasos a reproducir. Es el canal de registro: todo ticket nace o se documenta aquí.
- **Horario:** lunes a viernes de 9:00 a 20:00. Sábados de 10:00 a 14:00. Domingos solo S1 de clientes con add-on 24/7.

### 2.2 WhatsApp Business

- **Número:** el que aparece en la firma de emails y en Configuración → Soporte.
- **Uso:** incidencias urgentes en horario de servicio y seguimiento de un ticket ya abierto. No se atienden altas, bajas ni facturación por aquí.
- **Horario:** mismo que email. Fuera de horario, el bot acusa recibo y abre el ticket en la cola de email.

> **Regla de oro:** todo lo que entre por WhatsApp y requiera seguimiento se duplica en email. El email es el registro auditable; el WhatsApp es el canal ágil.

---

## 3. Tiempos de respuesta

Los tiempos se miden desde que el ticket entra en la cola. El SLA depende del plan del cliente y de la severidad.

### 3.1 Severidades

| Nivel | Definición | Ejemplo |
|-------|------------|---------|
| S1 — Crítico | No se puede fichar en absoluto | Terminal o backend caído |
| S2 — Mayor | Un método o grupo no puede fichar | NFC no lee para nadie, PIN sí |
| S3 — Menor | Funciona con workaround | Un empleado sin tarjeta |
| S4 — Consulta | Duda, no incidencia | Cómo exportar un informe |

### 3.2 SLA por plan

| Plan | S1 | S2 | S3 | S4 |
|------|----|----|----|----|
| Free | 24 h | 48 h | 72 h | Base de conocimiento |
| Pro (4,50 €/emp/mes) | 4 h | 8 h | 24 h | 48 h |
| Plus (6,50 €/emp/mes) | 2 h | 4 h | 12 h | 24 h |
| Add-on 24/7 (+2 €/emp/mes) | 1 h, cualquier día | 2 h | 4 h | 12 h |

El tiempo de **primera respuesta** es el que cuenta. La resolución puede tardar más si requiere escalado, pero el cliente recibe actualización cada 24 h hasta el cierre.

---

## 4. Flujo de un ticket

1. **Recepción.** El ticket entra por email o WhatsApp. Si llega por WhatsApp, el agente lo reenvía a la cola de email en 15 minutos.
2. **Clasificación.** El agente asigna severidad y plan. Esto fija el SLA.
3. **Primera respuesta.** Dentro del SLA: confirmar recepción, pedir la información mínima (ver §6) y dar la solución si es posible.
4. **Diagnóstico.** Si la primera respuesta no resuelve, seguir el árbol de la sección 6.
5. **Escalado.** Si L1 no resuelve en el tiempo del SLA o la incidencia es de infraestructura/firmware, escalar a L2 o L3 (ver §5).
6. **Resolución.** El ticket se cierra cuando el cliente confirma. Sin respuesta en 72 h, se cierra con nota de "sin confirmación".

---

## 5. Niveles de escalado

| Nivel | Quién | Resuelve | Herramientas |
|-------|-------|----------|--------------|
| **L1** | Agente de soporte | Consultas, configuración, reinicios guiados, reasignación de NFC, WiFi | Dashboard, WhatsApp, base de conocimiento |
| **L2** | Técnico de soporte | Sincronización, logs de terminal, rate limiting, cuenta, migración | Logs de backend, `curl` a la API, panel Railway |
| **L3** | Desarrollo / DevOps | Caídas de backend o BD, bugs de firmware ESP32, seguridad | Repositorio, Railway, Neon, GitHub Actions |

**Regla de escalado:** L1 escala a L2 si no resuelve en el SLA o si necesita logs del servidor. L2 escala a L3 solo si hay bug confirmado o caída de infraestructura. Nunca se salta de L1 a L3: el ticket pasa por L2 para dejar el contexto documentado.

---

## 6. Diagnóstico de las cuatro incidencias principales

### 6.1 Fichaje no funciona

El empleado acerca la tarjeta o teclea el PIN y el fichaje no aparece en el dashboard, o el terminal muestra error.

**Preguntas mínimas:** ¿Afecta a un empleado, a varios o a todos? ¿Qué método falla: NFC, PIN o QR? ¿El terminal tiene conexión? ¿Aparece algún mensaje en pantalla?

**Árbol:**

1. **Todos los empleados y todos los métodos** → S1. Pedir que abra el dashboard en el móvil. Si tampoco carga, escalar a L2/L3 (backend caído). Si el dashboard carga, problema de terminal: reiniciar (desenchufar 10 s). Si persiste, escalar a L2 para revisar logs de sincronización.
2. **Solo falla un método** → S2. Para NFC ver §6.2. Para PIN, comprobar que el empleado existe en el tenant correcto y que el PIN no está bloqueado por rate limiting (5 intentos fallidos → bloqueo 5 min). Si está bloqueado, esperar o resetear el PIN desde el dashboard.
3. **El fichaje se hace pero no aparece en el dashboard** → S2. El terminal está en modo offline. Comprobar WiFi. El ESP32 guarda en cola y sincroniza cada 30 s; si la conexión lleva más de 5 min caída, los registros se ven en el terminal pero no en la nube. Recuperar WiFi y esperar. Si tras 10 min no aparecen, escalar a L2 para revisar la cola offline.
4. **El fichaje aparece como incidencia** → S3. No es fallo: el empleado fichó fuera de turno o fuera de tolerancia. Revisar la configuración del turno (§6.4) o anotar el motivo en observaciones.

### 6.2 NFC no lee

El lector NFC ESP32 con módulo PN532 no detecta la tarjeta al acercarla.

**Preguntas mínimas:** ¿El lector tiene luz? ¿Cuál (verde, roja, azul)? ¿Afecta a una tarjeta o a todas? ¿El lector se ha movido, golpeado o mojado?

**Árbol:**

1. **Sin luz en el lector** → problema de alimentación. Comprobar cable USB-C y adaptador. Probar otro enchufe. Si no enciende, el lector está dañado: enviar reemplazo (gratuito en los primeros 12 meses, 49 € fuera de garantía).
2. **Luz azul fija** → el lector está en cola offline, sin conexión al backend. Es problema de red, no de NFC. Resolver como §6.1 punto 3.
3. **Luz verde/roja al acercar tarjeta pero "Tarjeta no reconocida"** → la tarjeta no está asignada. Reasignar desde Empleados → Tarjeta NFC → Asignar tarjeta (onboarding, día 5). Si dos tarjetas tienen el mismo UID, descartar una y usar otra del kit.
4. **El lector no reacciona a ninguna tarjeta** → reiniciar (desenchufar 10 s). Si persiste, el módulo PN532 puede estar desconectado internamente. Escalar a L2 para diagnóstico de firmware o envío de reemplazo.
5. **Solo una tarjeta no lee y el resto sí** → tarjeta dañada. Las NTAG213 cuestan 0,30 €/ud. El cliente puede pedir un pack de 10 (49 €) o usar el PIN como alternativa inmediata.

### 6.3 App no carga

El cliente no puede abrir el dashboard o el terminal se queda en blanco.

**Preguntas mínimas:** ¿El problema es en el móvil, en el ordenador o en el terminal de pared? ¿Aparece un error o pantalla en blanco? ¿Puede abrir otras webs?

**Árbol:**

1. **Si no puede abrir ninguna web** → problema de conexión del cliente. Pedir que reinicie el router. No escalar.
2. **Si solo falla app.talentup-fichaje.com** → S1 si afecta al terminal, S2 si solo es el dashboard. El agente L1 ejecuta `curl https://api.talentup-fichaje.com/api/health`. Si devuelve `status: ok`, el backend está bien y el problema es del navegador (caché, VPN, bloqueador). Pedir modo incógnito. Si el health check devuelve `503` o no responde → escalar a L2/L3 de inmediato. Es caída de plataforma.
3. **La pantalla del terminal de pared está en blanco** → S1. Reiniciar el terminal (desenchufar y enchufar). Si vuelve a colgar en 24 h, escalar a L2: puede ser memoria del dispositivo o versión cacheada del frontend.
4. **El dashboard carga pero una sección concreta no** → S3. Captura de pantalla, navegador y versión. Escalar a L2 con la captura.

### 6.4 Turno mal configurado

El cliente reporta que las horas no cuadran, que un empleado sale como incidencia o que el informe legal tiene datos erróneos.

**Preguntas mínimas:** ¿Qué empleado y qué fecha? ¿Qué turno tenía asignado y qué hora fichó realmente? ¿Tiene pausa obligatoria configurada y de cuánto?

**Árbol:**

1. **El empleado fichó dentro de su hora pero aparece como incidencia** → revisar la tolerancia de fichaje (Configuración → Tolerancia). Si está a 0, cualquier minuto fuera del inicio exacto genera incidencia. Ajustar a 10 minutos (valor por defecto).
2. **Las horas del informe no cuadran con las fichadas** → comprobar la pausa obligatoria. Si el convenio exige 30 min y no se configuró, las horas se calculan sin descontar la pausa. Añadir la pausa en Turnos → editar turno. El informe se recalcula automáticamente.
3. **Un empleado tiene turno asignado pero no le toca ese día** → error de calendario. Abrir Horarios → Calendario y verificar que el turno está en el día correcto. Si se usó Copiar semana, comprobar que no se copió un festivo como laborable.
4. **El informe legal no tiene todos los campos** → comprobar que el convenio colectivo está configurado (Configuración → Datos del restaurante → Convenio). Sin convenio, el cálculo de horas extras no se aplica. Tras corregir, re-exportar el PDF.
5. **El turno está bien pero el empleado insiste** → S3. Los fichajes son inmutables: no se editan, solo se anulan con motivo y log de auditoría. Si el fichaje es real (llegó tarde), anotar el motivo. Si es error de configuración, corregir el turno y recalcular; el fichaje original se mantiene y la anotación explica la diferencia.

---

## 7. FAQ técnico

**¿El sistema funciona sin internet?** Sí. El terminal guarda los fichajes en cola local (LittleFS en el ESP32) y sincroniza cada 30 segundos al recuperar conexión. El dashboard solo se actualiza cuando hay sincronización.

**¿Puedo editar un fichaje si me equivoqué?** No. Los fichajes son inmutables por cumplimiento del RD-ley 8/2019. Se anula el fichaje con motivo (queda log de auditoría) y, si es necesario, se registra uno correcto manualmente con justificación.

**¿Por qué se me bloquea el PIN?** El sistema bloquea el PIN tras 5 intentos fallidos en 1 minuto, durante 5 minutos. Si ocurre a menudo, resetear el PIN del empleado desde el dashboard.

**¿Cómo cambio el WiFi del lector NFC?** El WiFi se configura en el firmware del ESP32. Si el cliente cambia de red, hay que reconfigurar el ESP32. Es proceso L2: el agente L1 escala con el número de serie del lector (pegatina en la base).

**¿Cada cuánto se actualiza el sistema?** Las actualizaciones de backend y frontend son automáticas, sin intervención del cliente. El firmware del ESP32 se actualiza por OTA; el cliente recibe aviso por email.

**¿Puedo tener varios locales en una cuenta?** Sí. Cada local es un tenant independiente con su propio billing. Un Super Admin del grupo ve todos desde una vista consolidada.

---

## 8. Plantillas de primera respuesta

**S1/S2 (crítico/mayor):**

> Hola [Nombre]. He recibido tu incidencia sobre [resumen]. La he clasificado como [severidad] y estoy trabajando en ella. El SLA de tu plan es [tiempo]. Te respondo con diagnóstico o solución antes de [hora]. Mientras tanto, necesito: [información mínima]. — Equipo de Soporte TalentUP

**S3/S4 (menor/consulta):**

> Hola [Nombre]. Gracias por escribir. Tu consulta sobre [resumen] la atiendo yo. La solución rápida es: [pasos]. Si no te cuadra, dime y lo revisamos. — Equipo de Soporte TalentUP

---

## 9. Métricas de soporte

El equipo revisa semanalmente: tickets abiertos vs cerrados por severidad y plan, tiempo medio de primera respuesta vs SLA, % resueltos en L1 (objetivo: ≥70%), % escalados a L3 (objetivo: ≤10%) y reincidencias (mismo cliente, mismo problema en 30 días; objetivo: ≤5%). Cualquier desviación del 10% sobre el objetivo se revisa en el weekly y, si es recurrente, alimenta los pitfalls del onboarding o la base de conocimiento.