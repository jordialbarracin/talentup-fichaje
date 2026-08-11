# FAQ Cliente — TalentUP Fichaje

**Versión:** 1.0 — Agosto 2026
**Producto:** TalentUP Fichaje (SaaS de fichaje y control horario para hostelería)
**Cumplimiento:** RD-ley 8/2019, art. 34.9 ET — registro de jornada inmutable, conservación 4 años.

---

## Precio

### 1. ¿Cuánto cuesta TalentUP?

TalentUP se factura por **empleado activo y mes**, con tres planes:

| Plan | Precio mensual | Precio anual (≈15% descuento) |
|------|----------------|-------------------------------|
| Free | 0,00 € | 0,00 € |
| Pro | 4,50 €/empleado | 3,83 €/empleado (2 meses gratis) |
| Plus | 6,50 €/empleado | 5,53 €/empleado (2 meses gratis) |

La facturación anual premia la retención con el equivalente a dos meses gratuitos. El precio se sitúa por debajo de los generalistas de RR.HH. (Factorial, Kenjo) y al nivel del fichaje especializado (Sesame), pero con un producto vertical para hostelería.

### 2. ¿Hay versión gratuita?

Sí. El **Plan Free** es permanente (no es una prueba) e incluye:

- Hasta **5 empleados**.
- Fichaje por app móvil (GPS y código QR).
- Registro de jornada cumpliendo el RD-ley 8/2019.
- Exportación de informes básicos en PDF/Excel.
- 1 usuario administrador.
- Base de conocimiento y comunidad (sin soporte premium).

El Free está pensado para bares y restaurantes pequeños. Cuando el establecimiento crece o necesita gestión de turnos, escala al plan Pro.

### 3. ¿Qué descuentos ofrecen?

- **Anual:** 15% (2 meses gratis) sobre el precio del plan.
- **Volumen:** 11–25 empleados 5% adicional; 26–50 empleados 10% adicional; más de 50 tarifa negociada.
- **Migración:** 25% de descuento durante 3 meses para clientes que provengan de Sesame, Factorial o Kenjo.
- **Temporada baja (enero–marzo):** 1 mes gratis al contratar anual.

Los descuentos por volumen son acumulables con el anual, pero no con promociones de lanzamiento.

### 4. ¿Qué add-ons o módulos extra puedo contratar?

- **Comunicación Interna** (chat, tablón, push): 1,20 €/empleado/mes.
- **Formación** (microlearning y onboarding): 1,50 €/empleado/mes.
- **Bienestar y Encuestas** (clima laboral): 0,80 €/empleado/mes.
- **Cumplimiento Normativo** (alertas de convenio, horas extras): 1,00 €/empleado/mes.
- **Soporte 24/7**: 2,00 €/empleado/mes adicionales.
- **Nóminas**: vía partner (asesoría/gestoría); TalentUP no asume el servicio.
- **Onboarding premium**: 150–300 € por establecimiento.
- **Integración a medida con TPV/ERP**: 300–1.000 € según complejidad.

---

## NFC

### 5. ¿Cómo funciona el fichaje con NFC?

El terminal de pared lleva un lector **NFC basado en ESP32 con módulo PN532**. Cada empleado tiene una tarjeta **NTAG213** asignada a su perfil. Al acercar la tarjeta, el terminal registra entrada o salida con fecha y hora, muestra confirmación en pantalla y sincroniza con el dashboard.

La asignación de tarjetas se hace desde **Empleados → Tarjeta NFC → Asignar tarjeta** durante el onboarding. Cada tarjeta tiene un UID único vinculado a un empleado dentro del tenant.

### 6. ¿Qué hago si el lector NFC no lee las tarjetas?

El diagnóstico depende de la luz del lector:

- **Sin luz:** problema de alimentación. Revisar cable USB-C y adaptador, probar otro enchufe. Si no enciende, el lector está dañado: reemplazo gratuito en los primeros 12 meses, 49 € fuera de garantía.
- **Luz azul fija:** el lector está en cola offline sin conexión al backend. Es un problema de red, no de NFC.
- **Luz verde/roja pero "Tarjeta no reconocida":** la tarjeta no está asignada o dos tarjetas comparten UID. Reasignar desde el dashboard.
- **No reacciona a ninguna tarjeta:** reiniciar (desenchufar 10 s). Si persiste, escalar a soporte L2 para diagnóstico de firmware o envío de reemplazo.
- **Solo una tarjeta falla:** tarjeta dañada. Las NTAG213 cuestan 0,30 €/ud; el pack de 10 vale 49 €. Mientras tanto, el empleado puede usar su PIN.

### 7. ¿Puedo fichar sin tarjeta NFC?

Sí. TalentUP ofrece tres métodos de fichaje:

- **NFC** (tarjeta物理 al lector de pared).
- **PIN** numérico en el terminal.
- **QR** desde la app móvil (con geolocalización).

Si un empleado pierde o daña su tarjeta, puede usar el PIN de forma inmediata. El PIN se bloquea tras 5 intentos fallidos en 1 minuto, durante 5 minutos, como medida de seguridad. El administrador puede resetearlo desde el dashboard.

---

## Offline

### 8. ¿El sistema funciona sin internet?

Sí. El terminal de pared guarda los fichajes en una **cola local (LittleFS en el ESP32)** y sincroniza con el backend **cada 30 segundos** al recuperar conexión. Esto es crítico en hostelería, donde la caída de WiFi en hora punta no puede impedir el fichaje.

El dashboard de la nube solo refleja los registros una vez sincronizados. Si la conexión lleva más de 5 minutos caída, los fichajes se ven en el terminal pero todavía no en el panel. Al recuperar WiFi, la cola se vacía automáticamente.

### 9. ¿Cuánto tiempo guarda los datos offline el terminal?

El ESP32 almacena los fichajes en memoria persistente (LittleFS) hasta que se restablece la conexión y se completa la sincronización. No hay un límite estricto de horas: el terminal está diseñado para seguir registrando durante cortes prolongados. Si tras recuperar la conexión y esperar 10 minutos los registros no aparecen en el dashboard, hay que contactar con soporte para revisar la cola offline (escalamiento L2).

---

## Datos

### 10. ¿Cumple TalentUP con el RD-ley 8/2019?

Sí. TalentUP está diseñado específicamente para cumplir el **Real Decreto-ley 8/2019** y el art. 34.9 del Estatuto de los Trabajadores:

- Registro de jornada **inmutable**: los fichajes no se editan, solo se anulan con motivo y log de auditoría.
- Conservación de los registros durante **4 años** (plazo de prescripción de acciones laborales).
- Cálculo de horas extras según el convenio colectivo configurado.
- Exportación de informes legales en PDF con todos los campos requeridos.

Para que el informe legal sea completo, es necesario configurar el **convenio colectivo** en Configuración → Datos del restaurante → Convenio.

### 11. ¿Cuánto tiempo se conservan los datos de fichaje?

Los datos de fichaje se conservan **4 años** desde su registro, conforme al art. 21 del RD-ley 8/2019 y el art. 66 del Estatuto de los Trabajadores. Transcurrido ese plazo, los datos se suprimen de forma segura. La cancelación anticipada de la cuenta no acelera la supresión: los registros de jornada deben conservarse hasta el fin del plazo legal.

### 12. ¿Puedo editar o corregir un fichaje equivocado?

No se puede editar un fichaje existente. Por cumplimiento legal, **los fichajes son inmutables**. Si hay un error:

1. Se **anula** el fichaje incorrecto indicando un motivo (queda log de auditoría con usuario, fecha y razón).
2. Si es necesario, se **registra un fichaje manual** correcto con justificación.

Este flujo garantiza la trazabilidad que exige la Inspección de Trabajo. Si el error es de configuración del turno (no del fichaje real), se corrige el turno y el informe se recalcula automáticamente, manteniendo el fichaje original y la anotación que explica la diferencia.

---

## Seguridad

### 13. ¿Cómo protegen mis datos personales?

TalentUP aplica las medidas técnicas del Art. 32 del RGPD:

| Medida | Implementación |
|--------|----------------|
| Cifrado en tránsito | HTTPS / TLS 1.3 obligatorio |
| Cifrado en reposo | AES-256 (PostgreSQL) / SQLCipher (SQLite) |
| Hash de contraseñas | bcrypt |
| Autenticación | JWT con expiración |
| Control de acceso | Roles: super_admin, owner, manager |
| Aislamiento multi-tenant | Cada empresa solo ve sus datos |
| Auditoría | Log de operaciones críticas |

No se tratan datos especialmente protegidos (salud, ideología) ni datos de menores de edad.

### 14. ¿Tienen firmado un DPA?

Sí. TalentUP ofrece un **Acuerdo de Tratamiento de Datos (DPA)** conforme al Art. 28 del RGPD que regula la relación entre TalentUP (encargado) y la empresa cliente (responsable). El DPA incluye:

- Tratamiento solo bajo instrucción del responsable.
- Confidencialidad del personal con acceso.
- Notificación de violaciones de seguridad en menos de 24 h.
- Eliminación o devolución de datos al término del contrato.
- Facilitación de auditorías del responsable o de la AEPD.
- Notificación previa ante nuevos subencargados.

Los proveedores de infraestructura (PostgreSQL/Neon, Vercel/Cloudflare) actúan como encargados con DPA vigente.

### 15. ¿Quién puede ver los datos de mi empresa?

Gracias al **aislamiento multi-tenant**, cada empresa solo accede a sus propios datos. Dentro de cada cuenta, el acceso se controla por roles:

- **Super Admin**: ve todos los locales del grupo en una vista consolidada.
- **Owner**: gestión completa del establecimiento.
- **Manager**: gestión operativa sin acceso a configuración de facturación.

TalentUP no cede datos personales a terceros, salvo los proveedores de infraestructura necesarios para prestar el servicio. No se venden ni comparten datos con fines comerciales.

---

## Integraciones

### 16. ¿Se integra con mi TPV o software de gestión?

Sí, desde el **Plan Pro**. TalentUP ofrece integración con TPV y calendarios para sync de turnos y datos operativos. Para integraciones a medida con ERP o sistemas proprietarios, el coste oscila entre **300 € y 1.000 €** según complejidad, y se cotiza caso por caso.

La gestión de **nóminas** no es nativa: se ofrece vía partner (asesoría o gestoría integrada), con comisión de referenciación para TalentUP pero sin asumir el servicio de nómina.

### 17. ¿Puedo conectar TalentUP con otros sistemas por API?

Sí. El **Plan Plus** incluye **acceso a la API e integraciones avanzadas**. Esto permite conectar TalentUP con herramientas de BI, ERP, software de nóminas propio o flujos de automatización. El Plan Pro incluye integraciones estándar (TPV, calendarios) pero no acceso a la API completa.

Para casos de uso concretos, el equipo de soporte L2 puede facilitar la documentación de endpoints y ejemplos de integración.

---

## Soporte

### 18. ¿Cómo contacto con soporte y cuánto tardan en responder?

TalentUP atiende por dos canales:

- **Email:** `soporte@talentup-fichaje.com` — lunes a viernes de 9:00 a 20:00, sábados de 10:00 a 14:00.
- **WhatsApp Business:** para incidencias urgentes en horario de servicio y seguimiento de tickets ya abiertos.

El tiempo de **primera respuesta** depende del plan y la severidad:

| Plan | S1 (crítico) | S2 (mayor) | S3 (menor) | S4 (consulta) |
|------|--------------|------------|------------|---------------|
| Free | 24 h | 48 h | 72 h | Base de conocimiento |
| Pro | 4 h | 8 h | 24 h | 48 h |
| Plus | 2 h | 4 h | 12 h | 24 h |
| Add-on 24/7 | 1 h | 2 h | 4 h | 12 h |

Hasta la resolución, el cliente recibe actualización cada 24 h.

### 19. ¿Ofrecen soporte en horario nocturno o fines de semana?

El horario estándar es **lunes a viernes 9:00–20:00 y sábados 10:00–14:00**. El domingo solo se atiende a clientes con **add-on 24/7** (2,00 €/empleado/mes), que garantiza respuesta S1 en 1 hora cualquier día.

Para hostelería, que opera en horarios extendidos, el add-on 24/7 está recomendado en clientes con servicio nocturno o turnos de fin de semana. Fuera de horario, el bot de WhatsApp acusa recibo y abre el ticket en la cola de email para el siguiente turno.

### 20. ¿Qué pasa si el terminal de pared se avería?

- **Garantía (primeros 12 meses):** reemplazo gratuito del lector NFC.
- **Fuera de garantía:** 49 € el reemplazo del lector; 49 € el pack de 10 tarjetas NTAG213.
- **Mientras llega el reemplazo:** los empleados pueden fichar con **PIN en el terminal** (si el ESP32 funciona y solo falla el módulo NFC) o con **QR desde la app móvil** con geolocalización.

Para incidencias de firmware o hardware interno del ESP32, el soporte L2 diagnostica vía logs y, si confirma fallo, gestiona el envío del reemplazo. El proceso completo suele resolver en 48–72 h laborables dentro de la península.

---

*Para incidencias no resueltas en este FAQ, consulta la guía de soporte completa o escribe a `soporte@talentup-fichaje.com`.*