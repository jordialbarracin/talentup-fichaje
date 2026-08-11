# Documento de Demo — TalentUP Fichaje

**Guía de demostración comercial para clientes del sector hostelería**
**Duración:** 10 minutos · **Versión:** 1.0 · **Fecha:** 09 agosto 2026

---

## 1. Objetivo de la Demo

El objetivo de la demo no es enseñar todas las funcionalidades. Es **demostrar valor en 10 minutos**: que el cliente vea cómo TalentUP resuelve su problema de control horario, cumpla la ley sin fricción y le ahorre horas de gestión cada semana. La demo sigue una narrativa: **problema → setup → fichaje → control → cumplimiento → cierre**.

### Principios

- **Una historia, no un tour de features.** Usa el caso de La Tagliatella (restaurante italiano, Madrid, 10 empleados) como hilo conductor.
- **Muestra, no expliques.** Cada pantalla debe hablar por sí sola. Si tienes que explicar más de 30 segundos una pantalla, la estás enroscando.
- **Pregunta antes de mostrar.** Cada bloque empieza con una pregunta de descubrimiento. La respuesta del cliente condiciona el énfasis del bloque siguiente.
- **El cierre es una pregunta, no un descuento.** Termina pidiendo el siguiente paso, no vendiendo el plan.

### Preparación antes de la demo

1. **Entorno listo:** backend `localhost:8000` corriendo, frontend `localhost:3000`, terminal `localhost:3001`. Login demo: `owner@latagliatella.es` / `owner123`.
2. **Datos seed cargados:** 10 empleados, 3 turnos (Mañana/Tarde/Noche), calendario de julio con turnos asignados, 2 incidencias, 1 solicitud de vacaciones pendiente, 1 baja activa.
3. **Hardware físico:** lector NFC ESP32 CYD encendido y conectado, 2 tarjetas NFC asignadas (Carlos López — mañana, Ana Martínez — tarde).
4. **Pantalla compartida** a 1080p, navegador Chrome, zoom 100%. Cierra pestañas y notificaciones.

---

## 2. Script de Demo — 10 minutos

### Bloque 0 · Apertura y descubrimiento (0:00 – 1:30)

**Qué decir:**

> «Antes de enseñarte nada, cuéntame: ¿cómo lleváis ahora el control horario? ¿Excel, papel, una app que no os encaja?»

**Escucha y toma nota mental.** La respuesta determina dónde poner el énfasis:

| Respuesta del cliente | Énfasis en la demo |
|------------------------|---------------------|
| Papel / WhatsApp | Bloque 1 (fichaje) + Bloque 4 (informes) |
| Excel | Bloque 2 (turnos) + Bloque 4 (informes) |
| App generalista (Factorial, Sesame) | Bloque 2 (turnos hosteleros) + Bloque 3 (incidencias) |
| Nada / no lleva control | Bloque 1 + Bloque 4 (cumplimiento legal) |

**Pregunta de seguimiento:**

> «¿Cuántos empleados tenéis? ¿Tenéis turnos partidos o rotativos?»

Esto te dice si el cliente necesita el plan Pro (turnos avanzados) o le basta con el Free. No menciones precios todavía.

**Transición:**

> «Vale. Te voy a enseñar cómo funciona TalentUP con un restaurante real — La Tagliatella, 10 empleados, turnos de mañana, tarde y noche. Empezamos por donde lo viven los empleados: el fichaje.»

---

### Bloque 1 · Fichaje NFC + PIN (1:30 – 3:30)

**Qué mostrar (en este orden):**

1. **Terminal NFC** (`localhost:3001`) — pantalla «Terminal listo. Aproxime tarjeta o escanee QR.»
2. **Fichaje por NFC:** acerca la tarjeta de Carlos al lector. Pantalla muestra: **«Entrada registrada: Carlos López — 07:02»**.
3. **Fichaje por PIN:** pulsa «Fichar con PIN», introduce DNI `12345678A` + PIN `1234`, pulsa «Salida». Pantalla: **«Salida registrada: Carlos López — 15:05»**.
4. **PWA móvil:** abre `mobile/index.html` en el móvil o en una ventana estrecha. Muestra que el empleado puede fichar desde su propio teléfono, offline, y que los fichajes se sincronizan al recuperar WiFi.

**Qué decir:**

> «El empleado no tiene que aprender nada. Acerca la tarjeta y ficha. Si se le olvida la tarjeta, usa su PIN. Si no hay cobertura en cocina, la app guarda el fichaje y lo sincroniza cuando vuelve el WiFi. Esto es lo que más les cuesta a las apps generalistas: el fichaje en cocina, con manos sucias, sin WiFi. TalentUP está diseñado para eso.»

**Pregunta:**

> «¿Veis viable que vuestros empleados fichen así, o preferéis que cada uno use su móvil?»

---

### Bloque 2 · Dashboard + Turnos + Calendario (3:30 – 5:30)

**Qué mostrar:**

1. **Login en el panel** (`localhost:3000`) con `owner@latagliatella.es` / `owner123`.
2. **Dashboard:** stat-cards — «Fichados hoy: 4 de 10», «Pendientes: 6», «Incidencias: 1», «Vacaciones activas: Carlos 21–28 jul», «Horas acumuladas: 32 h». Di: «Esta es la pantalla que María ve cada mañana. En 5 segundos sabe quién ha fichado, quién falta y si hay algo que revisar.»
3. **Calendario:** semana del 20–26 de julio. Carlos en turno Mañana (naranja) lunes a viernes. Haz clic en el sábado de Carlos, asigna turno **Partido** (púrpura). La celda se colorea.
4. **Turnos:** abre la sección Turnos. Muestra el turno Partido — 10:00–23:00 con descanso 16:00–20:00. Di: «El sistema descuenta el descanso automáticamente del cálculo de horas. No hay que restar nada a mano.»

**Qué decir:**

> «El calendario es lo que sustituye al Excel de turnos. Arrastras, asignas, y cada empleado ve su turno en la app. Los festivos de tu comunidad se cargan solos — aquí San Isidro el 15 de mayo aparece marcado. No tienes que mantener un calendario laboral aparte.»

**Pregunta:**

> «¿Cuánto tiempo le dedicáis ahora a planificar turnos cada semana?»

---

### Bloque 3 · Incidencias y control (5:30 – 7:00)

**Qué mostrar:**

1. **Fichajes** — historial de hoy. Filtra por incidencia. Muestra a Carlos: Entrada 07:02, Salida 15:05, Total 7h 33m, Estado ✅ Normal.
2. Busca la incidencia: otro empleado que llegó tarde — Entrada 07:18, Estado ⚠️ Retraso (+18 min).
3. **Vacaciones:** sección Vacaciones. Solicitud pendiente de Ana Martínez — 1–15 ago, 11 días. Pulsa «Ver detalle», muestra saldo (30 días, 19 restantes), pulsa «Aprobar».

**Qué decir:**

> «Las incidencias no las buscas tú: el sistema te las pone delante. Retrasos, ausencias, salidas anticipadas. Y las vacaciones no se gestionan por WhatsApp: el empleado pide, tú apruebas o rechazas con motivo, y el saldo se actualiza solo.»

**Pregunta:**

> «¿Cómo gestionáis ahora las vacaciones? ¿Os llega algún empleado por WhatsApp pidiendo días?»

---

### Bloque 4 · Informes y cumplimiento RD-ley 8/2019 (7:00 – 8:30)

**Qué mostrar:**

1. **Informes** → tipo «Resumen de horas», periodo 1–31 julio 2026, todos los empleados. Pulsa **Generar PDF**. El navegador descarga `informe_horas_julio_2026.pdf`.
2. **Informe de inspección RD-ley 8/2019:** Informes → Inspección, segundo trimestre 2026. Pulsa **Generar informe RD-ley 8/2019**. Muestra que el PDF incluye datos del restaurante (CIF B12345678), listado diario de entradas/salidas, horas totales y firma digital del responsable.

**Qué decir:**

> «Este es el informe que te pide un inspector de trabajo. Listado diario, entrada y salida de cada empleado, horas totales, firma del responsable. Cumple el Real Decreto-ley 8/2019 y se conserva 4 años. Si mañana te llama Inspección, lo generas en 30 segundos. No tienes que ir a buscar papeles.»

**Pregunta:**

> «¿Habéis tenido ya una inspección de trabajo, o es algo que os preocupa?»

---

### Bloque 5 · Hardware, pricing y cierre (8:30 – 10:00)

**Qué mostrar:**

1. **Kit hardware físico:** enseña el lector NFC ESP32 CYD y las tarjetas. Di: «El kit cuesta 49 euros una sola vez. Lo enchufas, lo conectas al WiFi del local y funciona. No hay instalación ni cuota de mantenimiento del dispositivo.»
2. **Pricing** (`pricing.html` o menciona de memoria):

| Plan | Precio | Para quién |
|------|--------|------------|
| Free | 0 €/mes | Hasta 5 empleados, fichaje móvil, informes básicos |
| Pro | 4,50 €/empleado/mes | Empleados ilimitados, turnos avanzados, alertas, multi-sede |
| Plus | 6,50 €/empleado/mes | Todo + vacaciones, documentos firmados, API, gestor de cuenta |

> «El trial del Pro y el Plus es de 14 días sin tarjeta. Si tienes 10 empleados, el Pro te sale a 45 euros al mes. Menos de lo que cuesta una cena de equipo.»

**Preguntas de cierre:**

> 1. «¿Qué es lo que más te ha llamado la atención de lo que has visto?»
> 2. «¿Qué te preocupa o qué echas en falta?»
> 3. «¿Te parece bien si te preparo un trial de 14 días con vuestros datos reales y os damos soporte para configurar los turnos?»

**No vendas el plan. Vende el siguiente paso.** El trial es el compromiso. Si el cliente dice que sí al trial, la demo ha funcionado.

---

## 3. Preguntas frecuentes durante la demo

| Pregunta del cliente | Respuesta |
|----------------------|-----------|
| «¿Funciona sin internet?» | Sí. El terminal y la PWA guardan fichajes offline y sincronizan al recuperar conexión. |
| «¿Puedo exportar a mi gestoría?» | Sí, Excel con hojas separadas por horas, incidencias, vacaciones y extras. Tu asesoría lo abre sin problemas. |
| «¿Y si un empleado no tiene smartphone?» | Ficha con PIN en el terminal o con tarjeta NFC. No necesita móvil. |
| «¿Cumple el GDPR?» | Sí. RGPD y LOPDGDD. Conservación 4 años según RD-ley 8/2019. DPA disponible. |
| «¿Puedo dar acceso a mi gerente sin que vea todo?» | Sí, roles owner/manager/empleado con permisos diferenciados. |
| «¿Cuánto tarda en ponerse en marcha?» | Menos de 30 minutos. Asistente de 3 pasos: datos del local, turnos, empleados. |
| «¿Qué pasa si me cambio desde Factorial/Sesame?» | Promoción de migración: 25% de descuento durante 3 meses. Importamos tus datos. |

---

## 4. Errores a evitar

- **No abras la configuración.** Es aburrida y no vende. Solo si el cliente pregunta.
- **No enseñes las 9 secciones.** El cliente se satura. Dashboard, Calendario, Fichajes, Vacaciones, Informes. Las demás las mencionas.
- **No hables de la competencia sin que pregunten.** Si preguntan por Factorial/Sesame, posiciona: «Son buenos en RR.HH. general. Nosotros somos verticales en hostelería: turnos partidos, convenio, fichaje robusto en cocina.»
- **No improvises el fichaje NFC.** Practica el gesto antes de la demo. Si falla el lector, ten el PIN como plan B y di: «Así es como ficha un empleado sin tarjeta.»
- **No alargues más de 10 minutos.** Si el cliente pregunta mucho, agenda una segunda sesión. Una demo de 20 minutos pierde fuerza.

---

## 5. Checklist post-demo

- [ ] Enviar email de seguimiento en menos de 2 horas con: resumen de lo visto, enlace al trial, PDF de pricing, caso práctico de La Tagliatella.
- [ ] Crear el trial en el backend con los datos reales del cliente (nombre del restaurante, número de empleados, turnos).
- [ ] Programar llamada de onboarding a los 3 días del trial.
- [ ] Registrar en el CRM: tamaño del equipo, método de fichaje actual, objeciones, siguiente paso acordado.

---

*Documento interno — Equipo comercial TalentUP Fichaje*