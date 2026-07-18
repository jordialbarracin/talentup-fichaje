# Política de Privacidad — TalentUP Fichaje

**Última actualización:** Julio 2026

---

## 1. Responsable del Tratamiento

**TalentUP Fichaje**  
Contacto: privacidad@talentup.app

---

## 2. Datos que Recogemos

TalentUP Fichaje trata las siguientes categorías de datos personales de sus empleados-usuarios:

| Categoría | Datos concretos |
|-----------|-----------------|
| **Datos identificativos** | Nombre, apellidos, DNI/NIE, correo electrónico, teléfono |
| **Datos de fichaje** | Fecha, hora de entrada, hora de salida, pausas, incidencias |
| **Datos laborales** | Puesto, turno, centro de trabajo, horario asignado |
| **Datos de cuenta** | Usuario, hash de contraseña, rol, tenant al que pertenece |

No recogemos datos especialmente protegidos (salud, ideología, etc.) ni datos de menores de edad.

---

## 3. Finalidad del Tratamiento

Los datos se tratan exclusivamente para:

1. **Cumplimiento legal** — Registrar la jornada laboral según el Real Decreto-ley 8/2019 (obligación de registro de jornada en España).
2. **Gestión de personal** — Control horario, planificación de turnos, gestión de incidencias.
3. **Facturación** — Cálculo de horas trabajadas a efectos de nómina.
4. **Seguridad** — Autenticación, control de acceso y auditoría del sistema.

---

## 4. Base Legal

- **Art. 6.1.c) RGPD** — Obligación legal: RD-ley 8/2019 exige el registro de jornada.
- **Art. 6.1.b) RGPD** — Ejecución de un contrato: relación laboral entre empresa y empleado.
- **Art. 6.1.f) RGPD** — Interés legítimo: control horario y seguridad del sistema.

---

## 5. Plazo de Conservación

Los datos se conservan durante **4 años** desde su registro, conforme al artículo 21 del Real Decreto-ley 8/2019 y al artículo 66 del Estatuto de los Trabajadores (plazo de prescripción de acciones laborales).

Transcurrido ese plazo, los datos se suprimen de forma segura.

---

## 6. Destinatarios de los Datos

No cedemos datos personales a terceros, salvo:

- **Proveedores de infraestructura** (Neon — base de datos, Railway — hosting, Vercel — frontend) que actúan como encargados del tratamiento con los que tenemos contrato DPA vigente.
- **Obligación legal** — Fuerzas y cuerpos de seguridad, jueces y tribunales cuando exista requerimiento legal.

---

## 7. Derechos del Empleado

Puedes ejercer tus derechos ARCO-SUPOL (Acceso, Rectificación, Cancelación/Supresión, Oposición, Limitación, Portabilidad) dirigiéndote a:

**Email:** privacidad@talentup.app  
**O bien a través de tu empresa** (responsable del tratamiento directo)

| Derecho | Descripción |
|---------|-------------|
| **Acceso** | Saber qué datos tenemos tuyos y para qué los usamos |
| **Rectificación** | Corregir datos inexactos o incompletos |
| **Supresión** | Solicitar la eliminación de tus datos (salvo obligación legal de conservarlos) |
| **Oposición** | Oponerte al tratamiento para fines específicos |
| **Limitación** | Solicitar que restrinjamos el tratamiento |
| **Portabilidad** | Recibir tus datos en formato estructurado |

Responderemos a tu solicitud en un plazo máximo de **30 días**.

Si consideras que no hemos tratado tus datos conforme a la normativa, puedes presentar una reclamación ante la **Agencia Española de Protección de Datos (AEPD)**.

---

## 8. Medidas de Seguridad

Aplicamos las siguientes medidas técnicas y organizativas:

- **Cifrado en tránsito** — Todo el tráfico viaja por HTTPS/TLS 1.3.
- **Cifrado en reposo** — La base de datos está cifrada (Neon cifrado AES-256).
- **Hash de contraseñas** — Las contraseñas se almacenan hasheadas con bcrypt.
- **Autenticación JWT** — Tokens firmados con secreto único por tenant.
- **Control de acceso** — Roles (admin, manager, employee) con permisos granulares.
- **Auditoría** — Registro de todas las operaciones críticas (creación, modificación, eliminación de fichajes y usuarios).
- **Aislamiento multi-tenant** — Cada empresa (tenant) solo ve sus propios datos.
- **Copias de seguridad** — La base de datos se respalda diariamente con retención de 30 días.

---

## 9. Transferencias Internacionales

Los datos se almacenan en servidores ubicados en la **Unión Europea** (Neon — AWS Frankfurt, Alemania; Railway — EU). No realizamos transferencias internacionales fuera del EEE.

---

## 10. Cambios en esta Política

Actualizaremos esta política cuando sea necesario por cambios normativos o funcionales. Te notificaremos los cambios sustanciales a través de la aplicación o por correo electrónico.
