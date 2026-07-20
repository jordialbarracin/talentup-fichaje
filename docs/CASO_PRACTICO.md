# Caso Práctico: TalentUP Fichaje en La Tagliatella

**Protagonista:** María García, propietaria  
**Restaurante:** La Tagliatella (restaurante italiano en Madrid)  
**Dirección:** Calle Mayor 42, 28013 Madrid  
**Teléfono:** +34 912 345 678  
**CIF:** B12345678  
**Email:** owner@latagliatella.es / info@latagliatella.es  
**Backend:** http://localhost:8000/api  
**Frontend:** http://localhost:3000  
**Login propietaria:** `owner@latagliatella.es` / `owner123`  
**Convenio:** Hostelería  
**Plan:** Premium

---

## DÍA 1 — Recepción del Kit y alta del restaurante

### Mañana: María recibe el kit TalentUP

A las 09:30 el repartidor entrega una caja con:

- 1 tablet/dispositivo NFC TalentUP (cargador + soporte de pared)
- 10 tarjetas NFC blancas numeradas del 1 al 10
- Hoja con 10 códigos QR individuales
- Guía rápida impresa: *"Conecta, configura y empieza a fichar en 5 minutos"*

> **María:** *"Perfecto, hoy mismo lo pongo en marcha."*

### Paso 1 — Instalar el dispositivo

1. Desenrosca el soporte de pared y lo coloca junto a la entrada de cocina, a 1,20 m del suelo.
2. Conecta el cable USB-C al dispositivo y el cargador a la corriente.
3. En la pantalla de bienvenida del dispositivo aparece:

```
┌─────────────────────────────┐
│   TalentUP Fichaje v2.0      │
│   Configurar red WiFi        │
│                              │
│   Selecciona tu red:         │
│   ► LaTagliatella-Guest      │
│     Movistar_5G              │
│     Orange_Fibra             │
└─────────────────────────────┘
```

4. Pulsa sobre **LaTagliatella-Guest**.
5. Escribe la contraseña del restaurante y pulsa **Conectar**.
6. Pantalla de confirmación:

```
┌─────────────────────────────┐
│   ✅ Conectado a Internet     │
│   Sincronizando con la nube…  │
│                              │
│   [Continuar]                │
└─────────────────────────────┘
```

### Paso 2 — Crear cuenta de propietaria

1. Desde el portátil de la oficina, María abre Chrome y entra a:  
   **http://localhost:3000**
2. Aparece la pantalla de login:

```
┌───────────────────────────────┐
│   [LOGO] TalentUP Fichaje     │
│   Panel de gestión para       │
│   hostelería                  │
│                               │
│   ¿No tienes cuenta?          │
│   [Crear cuenta]              │
└───────────────────────────────┘
```

3. Pulsa **Crear cuenta**.
4. Rellena el formulario:

| Campo | Valor |
|---|---|
| Nombre del restaurante | `Restaurante La Tagliatella` |
| Tu nombre | `María García` |
| Correo electrónico | `owner@latagliatella.es` |
| Contraseña | `owner123` |
| Teléfono | `+34 912 345 678` |

5. Pulsa **Crear cuenta**.
6. El sistema responde:

```json
{
  "ok": true,
  "user": {
    "email": "owner@latagliatella.es",
    "name": "María García",
    "role": "owner"
  },
  "tenant_id": "<uuid-restaurante>",
  "is_new_tenant": true
}
```

> Tras el registro, el sistema crea automáticamente 3 turnos por defecto: Mañana, Tarde y Noche.

### Paso 3 — Configurar datos del restaurante

1. Aparece el asistente de configuración inicial en 3 pasos.
2. En el paso 1 completa:

| Campo | Valor |
|---|---|
| Nombre del restaurante | `Restaurante La Tagliatella` |
| Dirección | `Calle Mayor 42, Madrid` |
| Teléfono | `+34 912 345 678` |

3. Pulsa **Continuar**.
4. En el paso 2 revisa los turnos por defecto y pulsa **Saltar** (los creará ella al día siguiente).
5. En el paso 3 añade empleados y pulsa **Saltar**.
6. Finalmente entra al dashboard principal.

```
┌─────────────────────────────────────────┐
│  Dashboard                               │
│  Resumen ejecutivo de actividad          │
│                                          │
│  Empleados activos hoy:       0          │
│  Fichajes hoy:                0          │
│  Incidencias pendientes:      0          │
│  Horas extra esta semana:     0          │
└─────────────────────────────────────────┘
```

> **Resultado:** Restaurante dado de alta con rol `owner`, tenant activo y datos fiscales/dirección correctos.

---

## DÍA 2 — Configuración de turnos, empleados y métodos de fichaje

### Paso 1 — Crear los 5 turnos de La Tagliatella

1. En el menú lateral pulsa **Turnos**.
2. Aparecen los 3 turnos por defecto. Pulsa **Crear turno**.
3. Crea uno a uno:

#### Turno 1 — Mañana

| Campo | Valor |
|---|---|
| Nombre | `Mañana` |
| Código | `M` |
| Tipo | `morning` |
| Hora inicio | `07:00` |
| Hora fin | `15:00` |
| Descanso (min) | `30` |
| Tolerancia (min) | `5` |
| Color | `#FF6B35` |

Pulsa **Guardar**. Respuesta:

```json
{
  "id": "<uuid-morning>",
  "name": "Mañana",
  "code": "M",
  "start_time": "07:00:00",
  "end_time": "15:00:00",
  "tolerance_min": 5,
  "color": "#FF6B35"
}
```

#### Turno 2 — Tarde

| Campo | Valor |
|---|---|
| Nombre | `Tarde` |
| Código | `T` |
| Tipo | `afternoon` |
| Hora inicio | `15:00` |
| Hora fin | `23:00` |
| Descanso (min) | `30` |
| Tolerancia (min) | `5` |
| Color | `#0F766E` |

#### Turno 3 — Noche

| Campo | Valor |
|---|---|
| Nombre | `Noche` |
| Código | `N` |
| Tipo | `night` |
| Hora inicio | `23:00` |
| Hora fin | `07:00` |
| Descanso (min) | `30` |
| Tolerancia (min) | `10` |
| Plus nocturnidad | `25` |
| Color | `#1E3A5F` |

#### Turno 4 — Partido

| Campo | Valor |
|---|---|
| Nombre | `Partido` |
| Código | `P` |
| Tipo | `split` |
| Hora inicio | `10:00` |
| Hora fin | `23:00` |
| Inicio descanso | `16:00` |
| Fin descanso | `20:00` |
| Descanso (min) | `120` |
| Tolerancia (min) | `10` |
| Color | `#7C3AED` |

#### Turno 5 — Rotativo

| Campo | Valor |
|---|---|
| Nombre | `Rotativo` |
| Código | `R` |
| Tipo | `rotating` |
| Hora inicio | `07:00` |
| Hora fin | `15:00` |
| Descanso (min) | `30` |
| Tolerancia (min) | `5` |
| Es rotativo | ✅ |
| Color | `#F59E0B` |

4. Pantalla final de turnos:

```
┌────────────────────────────────────────────┐
│  Turnos configurados                       │
│                                            │
│  🟠 Mañana      07:00 → 15:00              │
│  🟢 Tarde       15:00 → 23:00              │
│  🔵 Noche       23:00 → 07:00 (+nocturnidad)│
│  🟣 Partido     10:00 → 23:00 (partido)    │
│  🟡 Rotativo    07:00 → 15:00 (rotativo)   │
└────────────────────────────────────────────┘
```

### Paso 2 — Dar de alta a los 10 empleados

1. En el menú lateral pulsa **Empleados**.
2. Pulsa **Añadir empleado**.
3. Crea los 10 empleados con los datos reales del sistema:

| # | Nombre | DNI | N.º SS | Categoría | Contrato | Jornada | Horas sem. | Turno | PIN |
|---|--------|-----|--------|-----------|----------|---------|-----------|-------|-----|
| 1 | Carlos López García | 12345678A | 28/12345678/00 | COC-03 | IND | completa | 40 | Mañana | 1234 |
| 2 | Ana Martínez Ruiz | 23456789B | 28/23456789/00 | SAL-03 | IND | completa | 40 | Tarde | 5678 |
| 3 | David Sánchez Pérez | 34567890C | 28/34567890/00 | COC-01 | IND | completa | 40 | Noche | 9012 |
| 4 | Laura Fernández López | 45678901D | 28/45678901/00 | SAL-01 | IND | completa | 40 | Mañana | 3456 |
| 5 | Javier Ruiz Gómez | 56789012E | 28/56789012/00 | BAR-02 | IND | completa | 40 | Tarde | 7890 |
| 6 | Sara Gómez Díaz | 67890123F | 28/67890123/00 | COC-04 | TEM-OC | parcial | 25 | Noche | 2345 |
| 7 | Pedro Díaz Martín | 78901234G | 28/78901234/00 | ADM-01 | IND | completa | 40 | Mañana | 6789 |
| 8 | Elena Torres Navarro | 89012345H | 28/89012345/00 | ADM-03 | IND | completa | 40 | Tarde | 0123 |
| 9 | Miguel Ángel Romero | 90123456I | 28/90123456/00 | MNT-01 | IND | completa | 40 | Noche | 4567 |
| 10 | Carmen Ruiz López | 01234567J | 28/01234567/00 | APR-01 | TEM-FOR | parcial | 20 | Mañana | 8901 |

Para cada empleado, el formulario incluye además:

- Nacionalidad: `Española`
- Fecha de alta (según contrato)
- IBAN bancario
- Grupo de cotización
- Base de cotización mensual
- Certificado de manipulador de alimentos (si aplica)

Ejemplo del cuerpo enviado para Carlos:

```json
{
  "name": "Carlos",
  "last_name": "López García",
  "full_name": "Carlos López García",
  "dni": "12345678A",
  "numero_ss": "28/12345678/00",
  "nationality": "Española",
  "birth_date": "1990-03-15",
  "phone": "+34 612 345 678",
  "email": "carlos.lopez@email.com",
  "address": "Calle Gran Vía 10, Madrid",
  "categoria_profesional": "COC-03",
  "tipo_contrato": "IND",
  "fecha_alta": "2023-01-15",
  "tipo_jornada": "completa",
  "horas_semanales": 40,
  "grupo_cotizacion": "10",
  "base_cotizacion": 1500,
  "coste_hora": 12.50,
  "iban": "ES91 2100 0418 4502 0005 1332",
  "pin": "1234",
  "shift_id": "<uuid-morning>",
  "food_handling_cert": true,
  "uniform_size": "M",
  "estado": "activo"
}
```

Respuesta del sistema:

```json
{
  "id": "<uuid-carlos>",
  "name": "Carlos",
  "full_name": "Carlos López García",
  "dni": "12345678A",
  "employee_code": "EMP-001",
  "pin_hash": "<bcrypt-hash>",
  "estado": "activo"
}
```

4. Pantalla de empleados tras darlos de alta:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Empleados            [Añadir empleado]                             │
├───────┬───────────┬──────────────┬──────────┬─────────┬─────┬───────┤
│Nombre │DNI        │N.º SS        │Categoría │Contrato │Turno│Estado │
├───────┼───────────┼──────────────┼──────────┼─────────┼─────┼───────┤
│Carlos │12345678A  │28/12345678/00│COC-03    │IND      │M    │Activo │
│Ana    │23456789B  │28/23456789/00│SAL-03    │IND      │T    │Activo │
│David  │34567890C  │28/34567890/00│COC-01    │IND      │N    │Activo │
│Laura  │45678901D  │28/45678901/00│SAL-01    │IND      │M    │Activo │
│Javier │56789012E  │28/56789012/00│BAR-02    │IND      │T    │Activo │
│Sara   │67890123F  │28/67890123/00│COC-04    │TEM-OC   │N    │Activo │
│Pedro  │78901234G  │28/78901234/00│ADM-01    │IND      │M    │Activo │
│Elena  │89012345H  │28/89012345/00│ADM-03    │IND      │T    │Activo │
│Miguel │90123456I  │28/90123456/00│MNT-01    │IND      │N    │Activo │
│Carmen │01234567J  │28/01234567/00│APR-01    │TEM-FOR  │M    │Activo │
└───────┴───────────┴──────────────┴──────────┴─────────┴─────┴───────┘
```

### Paso 3 — Asignar tarjetas NFC

1. En la lista de empleados, pulsa el botón **Editar** de Carlos.
2. En el campo **NFC UID** introduce el código de la tarjeta n.º 1:
   `04:A1:B2:C3:D4:E5`
3. Pulsa **Guardar**.
4. Repite para Ana (tarjeta n.º 2) y David (tarjeta n.º 3):

| Empleado | Tarjeta NFC | UID |
|---|---|---|
| Carlos López García | Tarjeta n.º 1 | `04:A1:B2:C3:D4:E5` |
| Ana Martínez Ruiz | Tarjeta n.º 2 | `04:A1:B2:C3:D4:E6` |
| David Sánchez Pérez | Tarjeta n.º 3 | `04:A1:B2:C3:D4:E7` |

5. María entrega físicamente las tarjetas a Carlos, Ana y David.

> **Pantalla del dispositivo tras registrar la tarjeta de Carlos:**
> ```
> ┌─────────────────────────────┐
> │  ✅ Tarjeta NFC vinculada   │
> │  Carlos López García          │
> │  UID: 04:A1:B2:C3:D4:E5     │
> │                             │
> │  [Volver]                   │
> └─────────────────────────────┘
> ```

### Paso 4 — Generar códigos QR para todos los empleados

1. En el menú lateral pulsa **Empleados**.
2. Pulsa el botón **Generar QR** situado junto a cada empleado.
3. El sistema genera un QR único vinculado al `employee_id`.
4. María imprime la hoja con los 10 códigos y los reparte:

| Código QR # | Empleado | Método de fichaje |
|---|---|---|
| QR-001 | Carlos López García | NFC + PIN + QR |
| QR-002 | Ana Martínez Ruiz | NFC + PIN + QR |
| QR-003 | David Sánchez Pérez | NFC + PIN + QR |
| QR-004 | Laura Fernández López | PIN + QR |
| QR-005 | Javier Ruiz Gómez | PIN + QR |
| QR-006 | Sara Gómez Díaz | PIN + QR |
| QR-007 | Pedro Díaz Martín | PIN + QR |
| QR-008 | Elena Torres Navarro | PIN + QR |
| QR-009 | Miguel Ángel Romero | PIN + QR |
| QR-010 | Carmen Ruiz López | PIN + QR |

> **Nota:** En el sistema el QR contiene simplemente el `employee_id`. El fichaje por QR se realiza contra `POST /api/clock/qr`.

---

## DÍA 3 — Primer día de fichajes reales

### 07:00 — Carlos llega y ficha con NFC

1. Carlos acerca la tarjeta n.º 1 al lector NFC del dispositivo.
2. El lector emite un *bip* de confirmación.
3. Pantalla del dispositivo:

```
┌─────────────────────────────┐
│   TalentUP Fichaje            │
│                               │
│   ✅ Carlos                   │
│   Entrada 07:03               │
│                               │
│   Turno: Mañana (07:00-15:00) │
│   Tolerancia: 5 min           │
│                               │
│   [OK]                        │
└─────────────────────────────┘
```

4. El sistema registra el fichaje. Detalle del POST a `/api/clock/nfc`:

```json
{
  "nfc_uid": "04:A1:B2:C3:D4:E5",
  "tenant_id": "<uuid-restaurante>"
}
```

Respuesta:

```json
{
  "ok": true,
  "message": "Carlos — Entrada registrada",
  "type": "in",
  "employee_name": "Carlos",
  "time": "2026-07-21T07:03:00+00:00"
}
```

> Aunque Carlos llegó a las 07:00, fichó a las 07:03 (dentro de los 5 min de tolerancia).

### 15:00 — Ana llega para el turno de tarde y ficha con PIN

1. Ana teclea su PIN `5678` en la pantalla numérica del dispositivo.
2. Pulsa **Entrar**.
3. Pantalla:

```
┌─────────────────────────────┐
│   ✅ Ana                      │
│   Entrada 15:02               │
│                               │
│   Turno: Tarde (15:00-23:00)  │
└─────────────────────────────┘
```

POST a `/api/clock`:

```json
{
  "pin": "5678",
  "type": "in",
  "tenant_id": "<uuid-restaurante>"
}
```

Respuesta:

```json
{
  "ok": true,
  "message": "Ana — Entrada registrada",
  "type": "in",
  "employee_name": "Ana",
  "time": "2026-07-21T15:02:00+00:00"
}
```

### 23:15 — David ficha con QR desde su móvil

1. David escanea su QR-003 con la app móvil de TalentUP.
2. El móvil envía:

```json
{
  "employee_id": "<uuid-david>",
  "tenant_id": "<uuid-restaurante>"
}
```

POST a `/api/clock/qr`.

3. El sistema responde:

```json
{
  "ok": true,
  "message": "David — Entrada registrada",
  "type": "in",
  "employee_name": "David",
  "time": "2026-07-21T23:15:00+00:00"
}
```

> David fichó 15 min tarde para el turno Noche (23:00). El sistema detecta incidencia "late".

### 15:00 — Carlos ficha salida

1. Carlos vuelve al dispositivo y pasa la tarjeta NFC.
2. El sistema detecta que ya tiene una entrada activa y registra automáticamente la salida.
3. Pantalla:

```
┌─────────────────────────────┐
│   ✅ Carlos                   │
│   Salida 15:05                │
│                               │
│   Horas trabajadas: 8h 2min   │
│   Descanso: 30 min            │
└─────────────────────────────┘
```

---

## DÍA 4 — Gestión diaria desde el dashboard

### 09:00 — María revisa el dashboard

1. Inicia sesión con `owner@latagliatella.es` / `owner123`.
2. Entra al **Dashboard**.
3. Pantalla de resumen del día anterior:

```
┌─────────────────────────────────────────┐
│  Dashboard                               │
├─────────────────────────────────────────┤
│  Empleados activos hoy:       10         │
│  Fichajes hoy:                8          │
│  Incidencias pendientes:      1          │
│  Horas extra esta semana:     0          │
├─────────────────────────────────────────┤
│  Sin fichar hoy:                         │
│  • Laura Fernández (M)                   │
│  • Miguel Ángel Romero (N)               │
├─────────────────────────────────────────┤
│  Vacaciones pendientes:                    │
│  • Ana Martínez: 1-15 agosto             │
│  • Laura Fernández: 1-10 septiembre        │
└─────────────────────────────────────────┘
```

4. Abajo, la tabla **Fichajes de hoy** muestra:

| Empleado | Tipo | Hora | Estado |
|---|---|---|---|
| Carlos López | Entrada | 07:03 | OK |
| Carlos López | Salida | 15:05 | OK |
| Ana Martínez | Entrada | 15:02 | OK |
| David Sánchez | Entrada | 23:15 | `LATE` |
| ... | ... | ... | ... |

5. María pulsa **Incidencias** en el menú y ve:

```
┌─────────────────────────────────────────┐
│  Incidencias                             │
├─────────────────────────────────────────┤
│  Tipo: LATE                              │
│  Empleado: David Sánchez Pérez           │
│  Fecha: 2026-07-21                       │
│  Descripción: Fichaje tarde (23:15)      │
│  Severidad: warning                      │
│  Estado: pendiente                       │
└─────────────────────────────────────────┘
```

> María decide hablar con David para la próxima semana.

### 11:30 — Carlos solicita vacaciones

1. Carlos envía un mensaje por WhatsApp a María:
   > *"María, quiero pedir vacaciones del 1 al 15 de agosto."*
2. María entra a **Vacaciones y Permisos** y pulsa **Nueva solicitud**.
3. Rellena:

| Campo | Valor |
|---|---|
| Empleado | `Carlos López García` |
| Tipo | `Vacaciones` |
| Fecha inicio | `2026-08-01` |
| Fecha fin | `2026-08-15` |
| Días totales | `11` |
| Motivo | `Vacaciones de verano` |

4. Pulsa **Guardar**. Estado inicial: `pending`.

POST a `/api/vacations`:

```json
{
  "employee_id": "<uuid-carlos>",
  "type": "vacation",
  "start_date": "2026-08-01",
  "end_date": "2026-08-15",
  "total_days": 11,
  "days_count_method": "working",
  "reason": "Vacaciones de verano"
}
```

Respuesta:

```json
{
  "id": "<uuid-vac-carlos>",
  "employee_id": "<uuid-carlos>",
  "start_date": "2026-08-01",
  "end_date": "2026-08-15",
  "total_days": 11,
  "status": "pending"
}
```

5. Aparece en la lista de solicitudes pendientes:

```
┌─────────────────────────────────────────┐
│  Solicitudes pendientes                  │
├─────────────────────────────────────────┤
│  Carlos López                            │
│  Vacaciones: 01/08/2026 → 15/08/2026    │
│  11 días · Vacaciones de verano          │
│  [Aprobar]  [Rechazar]                  │
└─────────────────────────────────────────┘
```

### 12:00 — María aprueba las vacaciones de Carlos

1. Pulsa **Aprobar**.
2. El sistema envía:

POST `/api/vacations/<uuid-vac-carlos>/approve`

Respuesta:

```json
{
  "id": "<uuid-vac-carlos>",
  "status": "approved",
  "approved_by": "<uuid-maria>",
  "approved_at": "2026-07-22T12:00:00+00:00"
}
```

3. Pantalla de confirmación:

```
┌─────────────────────────────┐
│  ✅ Vacaciones aprobadas     │
│  Carlos López                │
│  01/08/2026 → 15/08/2026    │
│  11 días hábiles             │
└─────────────────────────────┘
```

4. Carlos recibe notificación automática:
   > *"Tus vacaciones del 1 al 15 de agosto han sido aprobadas."*

### 13:15 — Javier llama: está enfermo

1. Javier llama a María:
   > *"María, no puedo venir hoy, el médico me ha dado baja por IT."*
2. María entra a **Bajas** y pulsa **Registrar baja**.
3. Rellena el formulario:

| Campo | Valor |
|---|---|
| Empleado | `Javier Ruiz Gómez` |
| Tipo de baja | `EC` (enfermedad común) |
| Fecha inicio | `2026-07-22` |
| Fecha prevista fin | `2026-07-29` |
| Días totales | `7` |
| Código diagnóstico | `J06.9` |
| Centro médico | `Hospital Clínico San Carlos` |
| Médico | `Dr. Martínez` |
| N.º parte | `PART-2026-002` |
| Mutua | `FREMAP` |

POST a `/api/leave`:

```json
{
  "employee_id": "<uuid-javier>",
  "leave_type": "EC",
  "start_date": "2026-07-22",
  "expected_end_date": "2026-07-29",
  "total_days": 7,
  "diagnosis_code": "J06.9",
  "medical_center": "Hospital Clínico San Carlos",
  "doctor_name": "Dr. Martínez",
  "part_number": "PART-2026-002",
  "mutua": "FREMAP",
  "is_work_accident": false,
  "is_professional_illness": false
}
```

Respuesta:

```json
{
  "id": "<uuid-leave-javier>",
  "employee_id": "<uuid-javier>",
  "leave_type": "EC",
  "status": "active",
  "start_date": "2026-07-22",
  "expected_end_date": "2026-07-29"
}
```

4. Pantalla de confirmación:

```
┌─────────────────────────────┐
│  ✅ Baja IT registrada       │
│  Javier Ruiz Gómez           │
│  EC · J06.9 · 7 días         │
│  Desde 22/07/2026            │
└─────────────────────────────┘
```

5. Javier recibe notificación:
   > *"Se ha registrado tu baja médica desde el 22 de julio."*

6. En el dashboard, el estado de Javier cambia a `badge-on-leave`.

---

## DÍA 5 — Cierre mensual: informes, exportaciones y costes

### 09:00 — María genera informe mensual de horas

1. Va a **Informes** → **Horas trabajadas**.
2. Selecciona:
   - Fecha desde: `2026-07-01`
   - Fecha hasta: `2026-07-31`
   - Empleado: `Todos`
3. Pulsa **Generar informe**.

GET `/api/reports/hours?date_from=2026-07-01&date_to=2026-07-31`

Respuesta resumida:

```json
{
  "date_from": "2026-07-01",
  "date_to": "2026-07-31",
  "tenant_id": "<uuid-restaurante>",
  "employees": [
    {
      "employee_id": "<uuid-carlos>",
      "employee_name": "Carlos",
      "total_hours": 168.50,
      "total_minutes": 10110,
      "days": 21,
      "daily_hours": { "2026-07-21": 8.03, ... }
    },
    {
      "employee_id": "<uuid-ana>",
      "employee_name": "Ana",
      "total_hours": 165.20,
      "total_minutes": 9912,
      "days": 21
    },
    ...
  ]
}
```

4. Pantalla del informe:

```
┌──────────────────────────────────────────────┐
│  Informe de horas · 01/07/2026 - 31/07/2026  │
├───────────────┬─────────────┬─────┬──────────┤
│ Empleado      │ Total horas │ Días│ Promedio │
├───────────────┼─────────────┼─────┼──────────┤
│ Carlos        │ 168.50h     │ 21  │ 8.02h    │
│ Ana           │ 165.20h     │ 21  │ 7.87h    │
│ David         │ 171.00h     │ 21  │ 8.14h    │
│ Laura         │ 160.00h     │ 21  │ 7.62h    │
│ Javier        │ 120.00h     │ 15  │ BAJA IT  │
│ ...           │ ...         │ ... │ ...      │
└───────────────┴─────────────┴─────┴──────────┘
```

### 09:30 — Exportar PDF para Inspección de Trabajo

1. En la misma pantalla de informes, pulsa **Exportar PDF**.
2. El sistema genera el PDF conforme al **RD-ley 8/2019 art. 34.9 ET**.
3. Cabecera del PDF:

```
TalentUP Fichaje — Informe de Registro
Período: 2026-07-01 a 2026-07-31
Empresa: Restaurante La Tagliatella
CIF: B12345678
Dirección: Calle Mayor 42, Madrid
Convenio: Hostelería
```

4. Contenido por empleado:

| Fecha | Entrada | Salida | Horas | Pausas |
|---|---|---|---|---|
| 2026-07-21 | 07:03 | 15:05 | 8.03 | 00:30 |
| 2026-07-22 | 07:00 | 15:00 | 8.00 | 00:30 |
| ... | ... | ... | ... | ... |

5. Pie de página:

> *"Documento generado por TalentUP Fichaje. Registro de jornada laboral conforme al RD-ley 8/2019 art. 34.9 ET. Conservación mínima: 4 años."*

6. El archivo descargado se llama `fichajes_2026-07-01_2026-07-31.pdf`.

GET `/api/reports/export?format=pdf&date_from=2026-07-01&date_to=2026-07-31`

### 09:45 — Exportar Excel para la gestoría

1. Pulsa **Exportar Excel**.
2. El sistema genera un `.xlsx` con una hoja por empleado:
   - Hoja resumen
   - Fichajes detallados (fecha, entrada, salida, horas)
   - Incidencias
   - Horas extras
3. Archivo descargado: `fichajes_2026-07-01_2026-07-31.xlsx`.

GET `/api/reports/export?format=excel&date_from=2026-07-01&date_to=2026-07-31`

4. María lo adjunta al email para su gestoría:
   > *"Buenos días, adjunto fichajes de julio 2026 en Excel. Saludos, María."*

### 10:15 — Revisar horas extras de David

1. Va a **Informes** → **Horas extras**.
2. Filtra por empleado `David Sánchez Pérez`.
3. El sistema muestra:

```
┌─────────────────────────────────────────┐
│  Horas extras · David Sánchez Pérez      │
├─────────────────────────────────────────┤
│  Fecha: 2026-07-02                      │
│  Tipo: Estructural                        │
│  Minutos: 90                              │
│  Multiplicador: 1.75                      │
│  Tarifa hora: 16.67 €                     │
│  Importe: 43.76 €                       │
│  Estado: Pendiente                        │
└─────────────────────────────────────────┘
```

4. María ve que David acumuló 90 min extra el 2 de julio por quedarse más tiempo tras el turno de noche.
5. Pulsa **Marcar como pagadas** o **Compensar con descanso** según acuerdo.

> **Nota:** El seed del sistema ya incluye esta hora extra de David con importe 43.76 €.

### 10:45 — Comprobar el coste laboral del mes

1. Va a **Informes** → **Costes laborales**.
2. Selecciona mes `7` y año `2026`.
3. El sistema consulta `GET /api/reports/labor-costs?month=7&year=2026`.
4. Respuesta:

```json
{
  "period": "7/2026",
  "summary": {
    "total_base_salary": 10500.00,
    "total_night_plus": 125.00,
    "total_holiday_plus": 250.00,
    "total_seniority_plus": 0.00,
    "total_overtime": 87.51,
    "total_gross": 10962.51,
    "total_ss_deduction": 666.75,
    "total_irpf_deduction": 1260.00,
    "total_net": 9035.76,
    "total_employees": 10
  },
  "employees": [
    {
      "name": "Carlos",
      "category": "COC-03",
      "base_salary": 1500.00,
      "overtime_amount": 43.75,
      "gross_total": 1543.75,
      "ss_deduction": 95.25,
      "irpf_deduction": 180.00,
      "net_total": 1268.50
    },
    {
      "name": "David",
      "category": "COC-01",
      "base_salary": 2000.00,
      "overtime_amount": 43.76,
      "gross_total": 2043.76,
      "ss_deduction": 127.00,
      "irpf_deduction": 240.00,
      "net_total": 1676.76
    },
    ...
  ]
}
```

5. Pantalla resumen:

```
┌─────────────────────────────────────────┐
│  Costes laborales · Julio 2026          │
├─────────────────────────────────────────┤
│  Base total:          10,500.00 €        │
│  Plus nocturnidad:       125.00 €        │
│  Plus festividad:        250.00 €        │
│  Horas extras:            87.51 €        │
│  ─────────────────────────────────────  │
│  Bruto total:         10,962.51 €        │
│  SS empleado (6.35%):   -666.75 €        │
│  IRPF (12%):          -1,260.00 €        │
│  ─────────────────────────────────────  │
│  Neto total:           9,035.76 €        │
│  Empleados:                 10             │
└─────────────────────────────────────────┘
```

6. María descarga también este informe en PDF y lo guarda junto a las nóminas.

### 11:00 — Cierre de la jornada de María

1. Vuelve al **Dashboard**.
2. El dashboard muestra el estado actualizado:

```
┌─────────────────────────────────────────┐
│  Dashboard                               │
├─────────────────────────────────────────┤
│  Empleados activos hoy:       10         │
│  Fichajes hoy:                6          │
│  Incidencias pendientes:      1          │
│  Horas extra esta semana:     1.5h       │
├─────────────────────────────────────────┤
│  Próximas ausencias:                     │
│  • Carlos: vacaciones 1-15 ago         │
│  • Javier: baja IT 22-29 jul           │
└─────────────────────────────────────────┘
```

3. María cierra sesión pulsando **Salir**.

---

## Resumen de endpoints utilizados

| Acción | Endpoint | Método |
|---|---|---|
| Login propietaria | `/api/auth/login` | POST |
| Registro restaurante | `/api/auth/register` | POST |
| Listar turnos | `/api/shifts` | GET |
| Crear turno | `/api/shifts` | POST |
| Listar empleados | `/api/employees` | GET |
| Crear empleado | `/api/employees` | POST |
| Editar empleado | `/api/employees/{id}` | PUT |
| Fichar con PIN | `/api/clock` | POST |
| Fichar con NFC | `/api/clock/nfc` | POST |
| Fichar con QR | `/api/clock/qr` | POST |
| Historial de fichajes | `/api/clock/history` | GET |
| Fichajes de hoy | `/api/clock/today` | GET |
| Listar vacaciones | `/api/vacations` | GET |
| Crear vacaciones | `/api/vacations` | POST |
| Aprobar vacaciones | `/api/vacations/{id}/approve` | POST |
| Listar bajas | `/api/leave` | GET |
| Crear baja | `/api/leave` | POST |
| Informe horas | `/api/reports/hours` | GET |
| Exportar informe | `/api/reports/export` | GET |
| Informe inspección | `/api/reports/inspection` | GET |
| Costes laborales | `/api/reports/labor-costs` | GET |
| Listar horas extra | `/api/overtime` | GET |

---

## Datos de acceso del caso práctico

### Cuenta propietaria

- **Email:** `owner@latagliatella.es`
- **Contraseña:** `owner123`
- **Rol:** `owner`

### Super admin (solo soporte TalentUP)

- **Email:** `admin@talentup.es`
- **Contraseña:** `admin123`
- **Rol:** `super_admin`

### PINs de empleados

| Empleado | PIN |
|---|---|
| Carlos López García | 1234 |
| Ana Martínez Ruiz | 5678 |
| David Sánchez Pérez | 9012 |
| Laura Fernández López | 3456 |
| Javier Ruiz Gómez | 7890 |
| Sara Gómez Díaz | 2345 |
| Pedro Díaz Martín | 6789 |
| Elena Torres Navarro | 0123 |
| Miguel Ángel Romero | 4567 |
| Carmen Ruiz López | 8901 |

### Tarjetas NFC asignadas

| Tarjeta | Empleado | UID |
|---|---|---|
| N.º 1 | Carlos | `04:A1:B2:C3:D4:E5` |
| N.º 2 | Ana | `04:A1:B2:C3:D4:E6` |
| N.º 3 | David | `04:A1:B2:C3:D4:E7` |

---

## Conclusión

En 5 días María ha completado el ciclo completo de TalentUP Fichaje:

1. **Día 1:** Recibió el kit, conectó el dispositivo, creó la cuenta y configuró el restaurante.
2. **Día 2:** Creó 5 turnos, dio de alta a 10 empleados con datos completos, asignó PINs, tarjetas NFC a 3 empleados y generó códigos QR para todos.
3. **Día 3:** Los empleados ficharon con NFC, PIN y QR. El sistema registró entradas/salidas y detectó incidencias.
4. **Día 4:** María gestionó el dashboard, aprobó vacaciones de Carlos y registró la baja IT de Javier.
5. **Día 5:** Generó informe mensual de horas, exportó PDF para Inspección de Trabajo, exportó Excel para la gestoría, revisó horas extras de David y comprobó el coste laboral del mes.

Todo el proceso cumple con el **RD-ley 8/2019 art. 34.9 ET**: registro diario de jornada, conservación de datos, inmutabilidad de fichajes y exportación para inspección.
