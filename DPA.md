# Acuerdo de Tratamiento de Datos (DPA)
## TalentUP Fichaje

**Version:** 1.0
**Fecha:** Agosto 2026

---

## 1. Partes

**Encargado del tratamiento:** TalentUP Fichaje (en adelante, "el Encargado")
**Responsable del tratamiento:** [Nombre de la empresa cliente] (en adelante, "el Responsable")

Este Acuerdo forma parte de los Terminos de Servicio de TalentUP Fichaje y se celebra conforme al Art. 28 del RGPD (Reglamento (UE) 2016/679).

---

## 2. Objeto y Alcance

Este DPA regula el tratamiento de datos personales que el Encargado realiza por cuenta del Responsable en la prestacion del servicio de fichaje digital y control horario.

**Datos tratados:**
- Datos identificativos: nombre, apellidos, DNI/NIE
- Datos de fichaje: fecha, hora entrada/salida, pausas
- Datos laborales: puesto, turno, centro de trabajo
- Datos de cuenta: usuario, hash contrasena, rol

**Categorias de interesados:** Empleados del Responsable

---

## 3. Instrucciones del Responsable

El Encargado tratara los datos unicamente siguiendo las instrucciones documentadas del Responsable. El Encargado no usara los datos para fines propios ni los cedera a terceros sin autorizacion expresa del Responsable.

---

## 4. Obligaciones del Encargado

1. **Tratar datos solo bajo instruccion** del Responsable (Art. 28.3 RGPD)
2. **Garantizar confidencialidad** del personal con acceso a datos (Art. 28.3.b)
3. **Aplicar medidas de seguridad** tecnicas y organizativas (Art. 32 RGPD)
4. **Notificar violaciones de seguridad** al Responsable en menos de 24h (Art. 33 RGPD)
5. **Eliminar o devolver datos** al termino del contrato
6. **Facilitar auditorias** del Responsable o de la AEPD
7. **Subencargados:** notificar al Responsable antes de contratar nuevos subencargados

---

## 5. Medidas de Seguridad

| Medida | Implementacion |
|--------|----------------|
| Cifrado en transito | HTTPS/TLS 1.3 obligatorio |
| Cifrado en reposo | AES-256 (PostgreSQL) / SQLCipher (SQLite) |
| Hash de contrasenas | bcrypt |
| Autenticacion | JWT con expiracion |
| Control de acceso | Roles: super_admin, owner, manager |
| Aislamiento multi-tenant | Cada empresa solo ve sus datos |
| Auditoria | Log de operaciones criticas |
| Backups | Diario, retencion 30 dias |
| Rate limiting | Proteccion contra fuerza bruta |

---

## 6. Subencargados

| Subencargado | Servicio | Ubicacion | DPA |
|--------------|----------|-----------|-----|
| Supabase | Base de datos PostgreSQL | EU (Frankfurt) | Si |
| Vercel | Hosting frontend/edge | EU | Si |
| Cloudflare | CDN/DNS | Global (EU nodes) | Si |

El Encargado notificara al Responsable cualquier cambio en subencargados con 30 dias de antelacion.

---

## 7. Violacion de Datos (Data Breach)

En caso de violacion de datos personales:

1. **Deteccion:** El Encargado detecta o es informado de la violacion
2. **Notificacion:** El Encargado notifica al Responsable en menos de 24 horas
3. **Contencion:** El Encargado toma medidas inmediatas para contener la violacion
4. **Documentacion:** El Encargado documenta la violacion (naturaleza, alcance, medidas)
5. **Cooperacion:** El Encargado coopera con el Responsable para notificar a la AEPD (72h) y a los afectados

---

## 8. Derechos de los Interesados

El Encargado asistira al Responsable en la atencion de solicitudes de derechos ARCO-SUPOL de los interesados:

- **Acceso:** Exportar datos del interesado
- **Rectificacion:** Modificar datos inexactos
- **Supresion:** Eliminar datos (salvo obligacion legal RD-ley 8/2019)
- **Oposicion:** Detener tratamiento para fines especificos
- **Limitacion:** Restringir tratamiento
- **Portabilidad:** Exportar en formato estructurado (JSON/CSV)

Plazo de respuesta: 30 dias desde la recepcion.

---

## 9. Auditoria y Control

El Responsable podra auditar el cumplimiento del Encargado:

1. **Auditoria documental:** Solicitar certificados de seguridad, politicas, procedimientos
2. **Auditoria tecnica:** Test de penetracion, revision de logs (previo acuerdo)
3. **Auditoria in situ:** Con 15 dias de preaviso y durante horas laborables

El Encargado facilitara toda la informacion necesaria para demostrar cumplimiento.

---

## 10. Duracion y Terminacion

- **Duracion:** Vigente mientras el Responsable use el servicio de TalentUP Fichaje
- **Terminacion:** A peticion de cualquiera de las partes con 30 dias de preaviso
- **Devolucion/borrado:** En 90 dias desde la terminacion, el Encargado devolvera o destruira todos los datos personales

---

## 11. Legislacion Aplicable

- **Normativa:** RGPD (UE 2016/679), LOPDGDD (Ley 3/2018), RD-ley 8/2019
- **Autoridad de control:** Agencia Espanola de Proteccion de Datos (AEPD)
- **Jurisdiccion:** Espana

---

## Contacto

**DPO / Contacto de proteccion de datos:** privacidad@talentup.app