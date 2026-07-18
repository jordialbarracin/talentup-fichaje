# TalentUP Fichaje — Arquitectura Completa de Producto

> **Versión:** 2.0 — Rediseño como SaaS comercializable de fichaje digital para hostelería
> **Convenio de referencia:** Convenio Colectivo de Hostelería (varía por CCAA, se parametriza por tenant)
> **Público objetivo:** Responsables de RRHH en hostelería (restaurantes, bares, hoteles, caterings)

---

## Índice

1. [Arquitectura de Datos Completa](#1-arquitectura-de-datos-completa)
2. [Estructura de Navegación del Dashboard](#2-estructura-de-navegación-del-dashboard)
3. [Flujos de Trabajo Principales](#3-flujos-de-trabajo-principales)
4. [Tipos de Datos del Convenio de Hostelería](#4-tipos-de-datos-del-convenio-de-hostelería)
5. [Reportes que Debe Generar](#5-reportes-que-debe-generar)
6. [Reglas de Negocio Transversales](#6-reglas-de-negocio-transversales)
7. [API Endpoints (Blueprint)](#7-api-endpoints-blueprint)

---

## 1. Arquitectura de Datos Completa

### 1.1 Tabla: `employees`

La tabla central. Un responsable de RRHH necesita gestionar **todos** estos datos de cada empleado.

```sql
-- ============================================================
-- TABLE: employees
-- Descripción: Datos completos del empleado de hostelería
-- ============================================================
CREATE TABLE employees (
    -- PK / Tenant
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_code   VARCHAR(20),           -- Código interno del empleado (ej: EMP-001)

    -- ===== DATOS PERSONALES =====
    first_name      VARCHAR(100) NOT NULL, -- Nombre
    last_name       VARCHAR(100) NOT NULL, -- Apellidos
    full_name       VARCHAR(200) NOT NULL, -- Nombre completo (cálculo o entrada)
    dni             VARCHAR(20),           -- DNI / NIE / Pasaporte
    nss             VARCHAR(20),           -- Número de Afiliación a la Seguridad Social
    nationality     VARCHAR(50),           -- Nacionalidad
    birth_date      DATE,                  -- Fecha de nacimiento
    gender          VARCHAR(20),           -- Género (Hombre, Mujer, No binario, No especifica)
    address         TEXT,                  -- Dirección completa
    city            VARCHAR(100),
    province        VARCHAR(100),
    postal_code     VARCHAR(10),
    phone           VARCHAR(20),           -- Teléfono móvil
    email           VARCHAR(200),          -- Email personal
    emergency_contact_name   VARCHAR(200), -- Contacto de emergencia
    emergency_contact_phone  VARCHAR(20),

    -- ===== DATOS LABORALES =====
    professional_category VARCHAR(100),    -- Categoría profesional (del convenio)
    contract_type    VARCHAR(50),          -- Tipo de contrato (ver sección 4.2)
    contract_start_date DATE,              -- Fecha de alta en la empresa
    contract_end_date DATE,                -- Fecha de fin de contrato (si temporal)
    contract_duration VARCHAR(50),         -- Duración del contrato (indefinido, temporal, etc.)
    contract_renewals INTEGER DEFAULT 0,   -- Número de renovaciones
    work_day_type    VARCHAR(50),          -- Tipo de jornada (completa, parcial, fijo-discontinuo)
    weekly_hours     NUMERIC(5,2),         -- Horas semanales según contrato
    daily_hours      NUMERIC(5,2),         -- Horas diarias según contrato
    seniority_date   DATE,                 -- Fecha de antigüedad (para cálculo de trienios)
    termination_date DATE,                 -- Fecha de baja (si aplica)
    termination_reason VARCHAR(200),       -- Motivo de baja
    rehire_eligible  BOOLEAN DEFAULT TRUE, -- Elegible para recontratación

    -- ===== DATOS DE FICHAJE =====
    pin_hash         VARCHAR(200) NOT NULL, -- PIN cifrado para fichar en terminal
    nfc_card_id      VARCHAR(100),          -- ID de tarjeta NFC
    nfc_uid          VARCHAR(50),           -- UID de la tarjeta NFC (lectura directa)
    photo_url        TEXT,                  -- URL de la foto del empleado
    fingerprint_hash VARCHAR(200),          -- Hash de huella dactilar (opcional)
    default_shift_id UUID REFERENCES shifts(id), -- Turno habitual
    clock_method     VARCHAR(20) DEFAULT 'pin', -- Método de fichaje: pin, nfc, fingerprint, face

    -- ===== DATOS DE VACACIONES =====
    vacation_annual_days NUMERIC(5,2) DEFAULT 30, -- Días de vacaciones anuales según convenio
    vacation_days_used   NUMERIC(5,2) DEFAULT 0,  -- Días de vacaciones usados este año
    vacation_days_pending NUMERIC(5,2) DEFAULT 30, -- Días pendientes (cálculo)
    vacation_year        INTEGER,                 -- Año de referencia de vacaciones
    vacation_notes       TEXT,                    -- Notas sobre vacaciones

    -- ===== DATOS BANCARIOS =====
    iban             VARCHAR(34),           -- IBAN para nómina
    bank_name        VARCHAR(100),
    bank_account_holder VARCHAR(200),       -- Titular de la cuenta

    -- ===== DATOS DE FORMACIÓN =====
    education_level  VARCHAR(100),         -- Nivel de estudios
    qualifications   TEXT,                  -- Titulaciones / certificados
    food_handling_cert BOOLEAN DEFAULT FALSE, -- Certificado de manipulación de alimentos
    food_handling_expiry DATE,             -- Caducidad del certificado
    allergies        TEXT,                  -- Alergias alimentarias (importante en hostelería)
    uniform_size     VARCHAR(20),           -- Talla de uniforme

    -- ===== ESTADO =====
    status           VARCHAR(20) DEFAULT 'active', -- Estado: active, inactive, on_vacation, on_leave, suspended
    is_active        BOOLEAN DEFAULT TRUE,
    is_available_for_scheduling BOOLEAN DEFAULT TRUE, -- Disponible para planificar turnos

    -- ===== AUDITORÍA =====
    created_by       UUID REFERENCES users(id),
    updated_by       UUID REFERENCES users(id),
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW(),

    -- ===== RESTRICCIONES =====
    UNIQUE(tenant_id, dni),
    UNIQUE(tenant_id, employee_code),
    UNIQUE(tenant_id, nss)
);

-- Índices
CREATE INDEX idx_employees_tenant ON employees(tenant_id);
CREATE INDEX idx_employees_status ON employees(tenant_id, status);
CREATE INDEX idx_employees_contract_end ON employees(tenant_id, contract_end_date)
    WHERE contract_end_date IS NOT NULL;
CREATE INDEX idx_employees_vacation ON employees(tenant_id, vacation_year);
```

### 1.2 Tabla: `contracts`

```sql
-- ============================================================
-- TABLE: contracts
-- Descripción: Histórico de contratos de cada empleado
-- ============================================================
CREATE TABLE contracts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    contract_type   VARCHAR(50) NOT NULL,  -- Tipo de contrato (ver 4.2)
    category        VARCHAR(100),           -- Categoría profesional al firmar
    start_date      DATE NOT NULL,          -- Fecha de inicio
    end_date        DATE,                   -- Fecha de fin (si temporal)
    duration_days   INTEGER,                -- Duración en días
    is_indefinite   BOOLEAN DEFAULT FALSE,  -- ¿Es indefinido?
    renewal_number  INTEGER DEFAULT 0,      -- Número de renovación
    previous_contract_id UUID REFERENCES contracts(id), -- Contrato anterior (encadenamiento)

    work_day_type   VARCHAR(50),            -- Tipo de jornada
    weekly_hours    NUMERIC(5,2),           -- Horas semanales
    daily_hours     NUMERIC(5,2),           -- Horas diarias
    salary_base     NUMERIC(10,2),          -- Salario base mensual
    salary_extras   NUMERIC(10,2),         -- Complementos salariales
    prorated_pages  NUMERIC(10,2),         -- Pagas prorrateadas

    document_url    TEXT,                   -- URL del PDF del contrato firmado
    signed_date     DATE,                   -- Fecha de firma
    notes           TEXT,

    status          VARCHAR(20) DEFAULT 'active', -- active, terminated, renewed
    termination_date DATE,
    termination_reason VARCHAR(200),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, employee_id, start_date)
);

CREATE INDEX idx_contracts_employee ON contracts(tenant_id, employee_id);
CREATE INDEX idx_contracts_active ON contracts(tenant_id, status)
    WHERE status = 'active';
```

### 1.3 Tabla: `shifts`

```sql
-- ============================================================
-- TABLE: shifts
-- Descripción: Tipos de turno configurables por el convenio
-- ============================================================
CREATE TABLE shifts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    name            VARCHAR(100) NOT NULL,  -- Nombre del turno (Mañana, Tarde, Noche, Partido, etc.)
    code            VARCHAR(20),            -- Código interno (M, T, N, P, R)
    shift_type      VARCHAR(30) NOT NULL,   -- Tipo: morning, afternoon, night, split, rotating, custom

    start_time      TIME NOT NULL,          -- Hora de inicio
    end_time        TIME NOT NULL,          -- Hora de fin
    break_start     TIME,                   -- Inicio de pausa (turnos partidos)
    break_end       TIME,                   -- Fin de pausa
    break_min       INTEGER DEFAULT 0,      -- Minutos de pausa obligatoria
    total_hours     NUMERIC(5,2),           -- Horas totales del turno (cálculo automático)

    tolerance_min   INTEGER DEFAULT 5,      -- Minutos de tolerancia para fichaje
    grace_period_min INTEGER DEFAULT 15,    -- Periodo de cortesía antes de considerar retraso
    overtime_threshold_min INTEGER DEFAULT 0, -- Minutos a partir de los cuales se considera extra

    is_split        BOOLEAN DEFAULT FALSE,  -- ¿Es turno partido?
    is_night        BOOLEAN DEFAULT FALSE,  -- ¿Es turno nocturno (22:00-06:00)?
    night_premium   NUMERIC(5,2) DEFAULT 0, -- % de plus de nocturnidad

    color           VARCHAR(7) DEFAULT '#FF6B35', -- Color para UI
    icon            VARCHAR(50),            -- Icono para UI

    is_active       BOOLEAN DEFAULT TRUE,
    sort_order      INTEGER DEFAULT 0,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_shifts_tenant ON shifts(tenant_id);
```

### 1.4 Tabla: `schedules`

```sql
-- ============================================================
-- TABLE: schedules
-- Descripción: Asignación de turnos a empleados por fecha
-- ============================================================
CREATE TABLE schedules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    shift_id        UUID NOT NULL REFERENCES shifts(id) ON DELETE CASCADE,

    date            DATE NOT NULL,          -- Fecha del turno
    is_rotating     BOOLEAN DEFAULT FALSE,  -- ¿Asignado por rotación automática?
    rotation_group  VARCHAR(50),            -- Grupo de rotación (A, B, C)
    is_holiday      BOOLEAN DEFAULT FALSE,  -- ¿Es día festivo?
    is_overtime     BOOLEAN DEFAULT FALSE,  -- ¿Es turno extra?
    notes           TEXT,

    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, employee_id, date)
);

CREATE INDEX idx_schedules_employee ON schedules(tenant_id, employee_id);
CREATE INDEX idx_schedules_date ON schedules(tenant_id, date);
CREATE INDEX idx_schedules_week ON schedules(tenant_id, date)
    WHERE date >= date_trunc('week', CURRENT_DATE);
```

### 1.5 Tabla: `clock_ins`

```sql
-- ============================================================
-- TABLE: clock_ins
-- Descripción: Registro inmutable de fichajes
-- NOTA: NO se editan, solo se anulan con motivo
-- ============================================================
CREATE TABLE clock_ins (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    type            VARCHAR(20) NOT NULL,   -- in, out, break_start, break_end
    timestamp       TIMESTAMPTZ NOT NULL,   -- Momento del fichaje
    scheduled_shift_id UUID REFERENCES shifts(id), -- Turno que tenía asignado ese día
    expected_start  TIMESTAMPTZ,            -- Hora esperada de inicio (del schedule)
    expected_end    TIMESTAMPTZ,            -- Hora esperada de fin (del schedule)

    -- Geolocalización
    latitude        NUMERIC(10,7),
    longitude       NUMERIC(10,7),
    geofence_id     UUID,                   -- ID de la geocerca donde fichó
    ip_address      VARCHAR(45),
    device_id       VARCHAR(100),           -- ID del terminal/tablet

    -- Offline
    is_offline      BOOLEAN DEFAULT FALSE,
    synced_at       TIMESTAMPTZ,

    -- Anulación (única forma de modificar)
    is_cancelled    BOOLEAN DEFAULT FALSE,
    cancel_reason   TEXT,
    cancelled_by    UUID REFERENCES users(id),
    cancelled_at    TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_clock_ins_employee ON clock_ins(tenant_id, employee_id);
CREATE INDEX idx_clock_ins_date ON clock_ins(tenant_id, timestamp);
CREATE INDEX idx_clock_ins_daily ON clock_ins(tenant_id, employee_id, DATE(timestamp));
```

### 1.6 Tabla: `holidays`

```sql
-- ============================================================
-- TABLE: holidays
-- Descripción: Festivos nacionales, autonómicos y locales
-- ============================================================
CREATE TABLE holidays (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    date            DATE NOT NULL,          -- Fecha del festivo
    name            VARCHAR(200) NOT NULL,  -- Nombre del festivo
    type            VARCHAR(30) NOT NULL,   -- national, regional, local
    region          VARCHAR(100),           -- Comunidad Autónoma (para autonómicos)
    locality        VARCHAR(100),           -- Localidad (para locales)
    is_paid         BOOLEAN DEFAULT TRUE,   -- ¿Es festivo retribuido?
    is_working      BOOLEAN DEFAULT FALSE,  -- ¿Se trabaja? (festivos de apertura comercial)
    year            INTEGER NOT NULL,       -- Año de referencia

    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, date)
);

CREATE INDEX idx_holidays_year ON holidays(tenant_id, year);
CREATE INDEX idx_holidays_date ON holidays(tenant_id, date);
```

### 1.7 Tabla: `vacation_requests`

```sql
-- ============================================================
-- TABLE: vacation_requests
-- Descripción: Solicitudes de vacaciones y permisos
-- ============================================================
CREATE TABLE vacation_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    type            VARCHAR(30) NOT NULL,   -- vacation, personal_leave, unpaid_leave, maternity,
                                            -- paternity, parental, marriage, moving, exam, training
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    total_days      NUMERIC(5,2) NOT NULL,  -- Días solicitados (cálculo: laborables o naturales)
    days_count_method VARCHAR(20) DEFAULT 'working', -- working: solo laborables, calendar: todos

    reason          TEXT,
    supporting_doc_url TEXT,                -- URL del justificante

    -- Estado de la solicitud
    status          VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected, cancelled
    approved_by     UUID REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    rejection_reason TEXT,

    -- Aprobación en cadena (si aplica)
    reviewed_by     UUID REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, employee_id, start_date, type)
);

CREATE INDEX idx_vacation_requests_employee ON vacation_requests(tenant_id, employee_id);
CREATE INDEX idx_vacation_requests_status ON vacation_requests(tenant_id, status);
CREATE INDEX idx_vacation_requests_dates ON vacation_requests(tenant_id, start_date, end_date);
```

### 1.8 Tabla: `leave`

```sql
-- ============================================================
-- TABLE: leave
-- Descripción: Bajas laborales (IT, maternidad, etc.)
-- ============================================================
CREATE TABLE leave (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    leave_type      VARCHAR(50) NOT NULL,   -- Tipo de baja (ver 4.6)
    start_date      DATE NOT NULL,
    end_date        DATE,                   -- NULL si sigue de baja
    expected_end_date DATE,                 -- Fecha prevista de alta
    total_days      INTEGER,                -- Días totales de baja

    -- Datos médicos
    diagnosis_code  VARCHAR(20),            -- CIE-10 / código diagnóstico
    medical_center  VARCHAR(200),           -- Centro médico / mutua
    doctor_name     VARCHAR(200),           -- Médico responsable
    part_number     VARCHAR(50),            -- Número de parte de baja
    mutua           VARCHAR(100),           -- Mutua colaboradora (MATEP)

    -- Datos laborales
    is_work_accident BOOLEAN DEFAULT FALSE, -- ¿Es accidente laboral?
    is_professional_illness BOOLEAN DEFAULT FALSE, -- ¿Es enfermedad profesional?
    has_leave_report BOOLEAN DEFAULT FALSE, -- ¿Tiene parte de baja?

    -- Documentación
    document_url    TEXT,                   -- URL del parte de baja escaneado
    medical_report_url TEXT,                -- URL del informe médico

    -- Estado
    status          VARCHAR(20) DEFAULT 'active', -- active, finished, extended
    extension_count INTEGER DEFAULT 0,      -- Número de prórrogas
    previous_leave_id UUID REFERENCES leave(id), -- Baja anterior (encadenamiento)

    -- Control
    notified_to_employee BOOLEAN DEFAULT FALSE,
    notified_to_ss       BOOLEAN DEFAULT FALSE, -- Notificado a Seguridad Social
    ss_communication_date DATE,             -- Fecha de comunicación a SS

    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leave_employee ON leave(tenant_id, employee_id);
CREATE INDEX idx_leave_active ON leave(tenant_id, status) WHERE status = 'active';
CREATE INDEX idx_leave_dates ON leave(tenant_id, start_date, end_date);
```

### 1.9 Tabla: `overtime`

```sql
-- ============================================================
-- TABLE: overtime
-- Descripción: Horas extras calculadas
-- ============================================================
CREATE TABLE overtime (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    date            DATE NOT NULL,          -- Fecha en que se realizaron
    shift_id        UUID REFERENCES shifts(id), -- Turno en que se generaron

    overtime_type   VARCHAR(30) NOT NULL,   -- structural, force_majeure (ver 4.4)
    total_minutes   INTEGER NOT NULL,       -- Minutos totales de extra
    compensated_minutes INTEGER DEFAULT 0,  -- Minutos compensados con descanso
    paid_minutes    INTEGER DEFAULT 0,     -- Minutos pagados en nómina
    hourly_rate_multiplier NUMERIC(4,2) DEFAULT 1.75, -- Multiplicador según convenio

    -- Cálculo económico
    hourly_rate     NUMERIC(10,2),          -- Precio hora ordinaria
    overtime_amount NUMERIC(10,2),          -- Importe de la hora extra

    -- Compensación
    compensation_type VARCHAR(20) DEFAULT 'pending', -- pending, paid, compensated_with_rest
    compensated_date DATE,                  -- Fecha de compensación
    payroll_id      UUID REFERENCES payroll(id), -- Vinculación a nómina

    -- Origen
    source          VARCHAR(30) DEFAULT 'auto', -- auto: detectado automáticamente, manual
    approved_by     UUID REFERENCES users(id),
    notes           TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_overtime_employee ON overtime(tenant_id, employee_id);
CREATE INDEX idx_overtime_date ON overtime(tenant_id, date);
CREATE INDEX idx_overtime_pending ON overtime(tenant_id, compensation_type)
    WHERE compensation_type = 'pending';
```

### 1.10 Tabla: `payroll`

```sql
-- ============================================================
-- TABLE: payroll
-- Descripción: Cálculo mensual de horas → importe para nómina
-- ============================================================
CREATE TABLE payroll (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    -- Periodo
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,        -- 1-12
    period_label    VARCHAR(20),            -- "Enero 2025", "Febrero 2025", etc.

    -- Datos del empleado en el periodo
    contract_type   VARCHAR(50),
    professional_category VARCHAR(100),
    work_day_type   VARCHAR(50),
    weekly_hours    NUMERIC(5,2),

    -- ===== HORAS TRABAJADAS =====
    -- Horas ordinarias
    scheduled_hours      NUMERIC(10,2) DEFAULT 0, -- Horas programadas
    worked_hours         NUMERIC(10,2) DEFAULT 0, -- Horas realmente trabajadas
    worked_days          INTEGER DEFAULT 0,       -- Días trabajados
    absent_days          INTEGER DEFAULT 0,       -- Días de ausencia
    holiday_hours        NUMERIC(10,2) DEFAULT 0, -- Horas en festivos

    -- Horas extraordinarias
    overtime_structural  NUMERIC(10,2) DEFAULT 0, -- Horas extra estructurales
    overtime_force_majeure NUMERIC(10,2) DEFAULT 0, -- Horas extra fuerza mayor
    overtime_total       NUMERIC(10,2) DEFAULT 0, -- Total horas extra
    overtime_amount      NUMERIC(10,2) DEFAULT 0, -- Importe horas extra

    -- Incidencias
    late_minutes         INTEGER DEFAULT 0,
    early_leave_minutes  INTEGER DEFAULT 0,
    no_show_days         INTEGER DEFAULT 0,

    -- ===== CÁLCULO ECONÓMICO =====
    -- Salario base
    base_salary          NUMERIC(10,2) DEFAULT 0, -- Salario base del periodo
    salary_prorated      NUMERIC(10,2) DEFAULT 0, -- Pagas prorrateadas

    -- Complementos
    night_plus           NUMERIC(10,2) DEFAULT 0, -- Plus de nocturnidad
    holiday_plus         NUMERIC(10,2) DEFAULT 0, -- Plus de festividad
    seniority_plus       NUMERIC(10,2) DEFAULT 0, -- Plus de antigüedad (trienios)
    toxicity_plus        NUMERIC(10,2) DEFAULT 0, -- Plus de toxicidad / peligrosidad
    responsibility_plus  NUMERIC(10,2) DEFAULT 0, -- Plus de responsabilidad
    transport_plus       NUMERIC(10,2) DEFAULT 0, -- Plus de transporte
    meal_plus            NUMERIC(10,2) DEFAULT 0, -- Plus de comida / manutención

    -- Deducciones
    ss_deduction         NUMERIC(10,2) DEFAULT 0, -- Deducción Seguridad Social
    irpf_deduction       NUMERIC(10,2) DEFAULT 0, -- Deducción IRPF
    other_deductions     NUMERIC(10,2) DEFAULT 0, -- Otras deducciones (embargos, etc.)

    -- Totales
    gross_total          NUMERIC(10,2) DEFAULT 0, -- Total bruto
    net_total            NUMERIC(10,2) DEFAULT 0, -- Total neto (a percibir)

    -- Estado
    status               VARCHAR(20) DEFAULT 'draft', -- draft, calculated, approved, paid
    approved_by          UUID REFERENCES users(id),
    approved_at          TIMESTAMPTZ,
    paid_at              TIMESTAMPTZ,
    payment_method       VARCHAR(50),        -- transferencia, cheque, efectivo
    payment_reference    VARCHAR(100),       -- Referencia de la transferencia

    -- Documentos
    payroll_document_url TEXT,               -- URL del PDF de nómina generado
    settlement_document_url TEXT,            -- URL del finiquito (si aplica)

    notes                TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, employee_id, year, month)
);

CREATE INDEX idx_payroll_employee ON payroll(tenant_id, employee_id);
CREATE INDEX idx_payroll_period ON payroll(tenant_id, year, month);
CREATE INDEX idx_payroll_status ON payroll(tenant_id, status);
```

### 1.11 Tabla: `notifications`

```sql
-- ============================================================
-- TABLE: notifications
-- Descripción: Avisos y notificaciones a empleados y gestores
-- ============================================================
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Destinatario
    recipient_type  VARCHAR(20) NOT NULL,   -- employee, manager, all_managers, all_employees
    employee_id     UUID REFERENCES employees(id), -- NULL si es para todos
    user_id         UUID REFERENCES users(id),     -- NULL si es para empleados

    -- Contenido
    type            VARCHAR(50) NOT NULL,   -- Tipo de notificación (ver abajo)
    title           VARCHAR(200) NOT NULL,
    message         TEXT NOT NULL,
    priority        VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    category        VARCHAR(50),            -- clocking, vacation, leave, payroll, incident, system

    -- Acción
    action_url      TEXT,                   -- URL a la que lleva al hacer clic
    action_label    VARCHAR(100),           -- Texto del botón de acción

    -- Estado
    is_read         BOOLEAN DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    is_dismissed    BOOLEAN DEFAULT FALSE,
    sent_via        VARCHAR(50),            -- in_app, email, sms, push

    -- Programación
    scheduled_for   TIMESTAMPTZ,            -- Para notificaciones programadas
    sent_at         TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Tipos de notificación predefinidos:
-- clock_reminder: Recordatorio de fichar
-- late_clock: Aviso de fichaje tardío
-- missing_clock: No ha fichado
-- vacation_request: Nueva solicitud de vacaciones
-- vacation_approved: Vacaciones aprobadas
-- vacation_rejected: Vacaciones rechazadas
-- leave_start: Inicio de baja
-- leave_end: Fin de baja
-- contract_expiry: Próximo vencimiento de contrato
-- document_expiry: Próxima caducidad de documento
-- payroll_ready: Nómina disponible
-- overtime_approved: Horas extra aprobadas
-- incident_new: Nueva incidencia
-- incident_resolved: Incidencia resuelta
-- schedule_change: Cambio en el horario
-- holiday_reminder: Recordatorio de festivo

CREATE INDEX idx_notifications_recipient ON notifications(tenant_id, employee_id);
CREATE INDEX idx_notifications_unread ON notifications(tenant_id, is_read)
    WHERE is_read = FALSE;
CREATE INDEX idx_notifications_type ON notifications(tenant_id, type);
```

### 1.12 Tabla: `work_calendar`

```sql
-- ============================================================
-- TABLE: work_calendar
-- Descripción: Calendario laboral por año
-- ============================================================
CREATE TABLE work_calendar (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    year            INTEGER NOT NULL,       -- Año del calendario
    date            DATE NOT NULL,           -- Fecha concreta

    day_type        VARCHAR(20) NOT NULL,   -- working, holiday, weekend, special
    is_working_day  BOOLEAN DEFAULT TRUE,   -- ¿Es día laborable?
    is_holiday      BOOLEAN DEFAULT FALSE,  -- ¿Es festivo?
    is_weekend      BOOLEAN DEFAULT FALSE,  -- ¿Es fin de semana?

    holiday_id      UUID REFERENCES holidays(id), -- Vinculación a festivo (si aplica)
    holiday_name    VARCHAR(200),            -- Nombre del festivo (copia para consultas rápidas)

    -- Configuración especial
    opening_time    TIME,                    -- Hora de apertura (si aplica)
    closing_time    TIME,                    -- Hora de cierre
    requires_special_schedule BOOLEAN DEFAULT FALSE, -- ¿Requiere horario especial?
    notes           TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, date)
);

CREATE INDEX idx_work_calendar_year ON work_calendar(tenant_id, year);
CREATE INDEX idx_work_calendar_holidays ON work_calendar(tenant_id, is_holiday)
    WHERE is_holiday = TRUE;
```

### 1.13 Tabla: `incidents`

```sql
-- ============================================================
-- TABLE: incidents
-- Descripción: Incidencias auto-detectadas o reportadas
-- ============================================================
CREATE TABLE incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    date            DATE NOT NULL,
    incident_type   VARCHAR(50) NOT NULL,   -- Tipo de incidencia (ver 4.6)
    description     TEXT,
    severity        VARCHAR(20) DEFAULT 'warning', -- info, warning, critical

    -- Datos de contexto
    clock_in_id     UUID REFERENCES clock_ins(id), -- Fichaje relacionado (si aplica)
    schedule_id     UUID REFERENCES schedules(id),  -- Horario relacionado (si aplica)
    shift_id        UUID REFERENCES shifts(id),    -- Turno relacionado

    -- Resolución
    is_resolved     BOOLEAN DEFAULT FALSE,
    resolution      TEXT,                    -- Descripción de la resolución
    resolved_by     UUID REFERENCES users(id),
    resolved_at     TIMESTAMPTZ,

    -- Origen
    source          VARCHAR(20) DEFAULT 'auto', -- auto, manual, employee_report
    reported_by     UUID REFERENCES users(id),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_incidents_employee ON incidents(tenant_id, employee_id);
CREATE INDEX idx_incidents_unresolved ON incidents(tenant_id, is_resolved)
    WHERE is_resolved = FALSE;
CREATE INDEX idx_incidents_date ON incidents(tenant_id, date);
```

### 1.14 Tabla: `tenants` (ampliada)

```sql
-- ============================================================
-- TABLE: tenants
-- Descripción: Establecimiento / empresa (multi-tenant)
-- ============================================================
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,   -- Nombre comercial
    legal_name      VARCHAR(200),            -- Razón social
    cif             VARCHAR(20),              -- CIF / NIF
    address         TEXT,
    city            VARCHAR(100),
    province        VARCHAR(100),
    postal_code     VARCHAR(10),
    phone           VARCHAR(20),
    email           VARCHAR(100),
    website         VARCHAR(200),

    -- Datos de convenio
    convenio        VARCHAR(100) DEFAULT 'hosteleria', -- Convenio colectivo aplicable
    ccaa            VARCHAR(100),            -- Comunidad Autónoma (para festivos)
    locality        VARCHAR(100),            -- Localidad (para festivos locales)
    sector          VARCHAR(100),            -- Subsector: restaurante, bar, hotel, catering

    -- Configuración de fichaje
    tolerancia_min  INTEGER DEFAULT 5,       -- Tolerancia general en minutos
    default_grace_period INTEGER DEFAULT 15, -- Periodo de cortesía general
    auto_detect_incidents BOOLEAN DEFAULT TRUE,
    require_geolocation BOOLEAN DEFAULT FALSE,
    require_photo_on_clock BOOLEAN DEFAULT FALSE,
    allow_offline_clock BOOLEAN DEFAULT TRUE,
    max_offline_hours INTEGER DEFAULT 24,    -- Máximo horas offline permitido

    -- Configuración de vacaciones
    vacation_days_per_year NUMERIC(5,2) DEFAULT 30, -- Días de vacaciones por año
    vacation_accrual VARCHAR(20) DEFAULT 'calendar', -- calendar: por año natural, contract: desde alta
    vacation_requires_approval BOOLEAN DEFAULT TRUE,
    min_vacation_days_before INTEGER DEFAULT 15, -- Mínimo días de antelación para solicitar
    max_consecutive_vacation_days INTEGER DEFAULT 30,

    -- Configuración de nómina
    payroll_day     INTEGER DEFAULT 30,      -- Día de pago
    payroll_period  VARCHAR(20) DEFAULT 'monthly', -- monthly, biweekly
    irpf_default    NUMERIC(5,2),            -- % IRPF por defecto
    ss_employee_percent NUMERIC(5,2) DEFAULT 6.35, -- % SS a cargo del empleado
    ss_company_percent  NUMERIC(5,2) DEFAULT 29.90, -- % SS a cargo de la empresa

    -- Plan / Billing
    plan            VARCHAR(20) DEFAULT 'basic', -- basic, pro, enterprise
    max_employees   INTEGER DEFAULT 50,
    features        JSONB,                   -- Características habilitadas
    billing_email   VARCHAR(200),
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),

    -- Estado
    is_active       BOOLEAN DEFAULT TRUE,
    setup_completed BOOLEAN DEFAULT FALSE,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.15 Tabla: `users` (ampliada)

```sql
-- ============================================================
-- TABLE: users
-- Descripción: Usuarios del sistema (gestores, admins)
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE, -- NULL para super_admin
    email           VARCHAR(200) NOT NULL UNIQUE,
    password_hash   VARCHAR(200) NOT NULL,
    name            VARCHAR(200) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'owner',
                    -- super_admin: ve todos los tenants
                    -- owner: dueño del restaurante, acceso completo
                    -- manager: encargado, acceso limitado
                    -- viewer: solo lectura (inspector, contable)

    -- Permisos granulares (para manager/viewer)
    permissions     JSONB,                   -- {"employees": "read", "payroll": "none", ...}

    -- Datos de contacto
    phone           VARCHAR(20),
    avatar_url      TEXT,
    language        VARCHAR(10) DEFAULT 'es',
    timezone        VARCHAR(50) DEFAULT 'Europe/Madrid',

    -- 2FA
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(100),

    -- Estado
    is_active       BOOLEAN DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    last_login_ip   VARCHAR(45),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.16 Tabla: `audit_log` (ampliada)

```sql
-- ============================================================
-- TABLE: audit_log
-- Descripción: Registro de auditoría (inmutable)
-- ============================================================
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id),
    employee_id     UUID REFERENCES employees(id), -- Si la acción afecta a un empleado

    action          VARCHAR(100) NOT NULL,   -- create, update, delete, cancel, approve, reject, export
    entity_type     VARCHAR(50) NOT NULL,   -- employee, contract, shift, schedule, clock_in, etc.
    entity_id       UUID,

    old_value       JSONB,                   -- Valor anterior (para updates)
    new_value       JSONB,                   -- Valor nuevo (para creates/updates)
    changes         JSONB,                   -- Solo los campos que cambiaron

    ip_address      VARCHAR(45),
    user_agent      TEXT,
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_tenant ON audit_log(tenant_id);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
```

### 1.17 Tabla: `geofences`

```sql
-- ============================================================
-- TABLE: geofences
-- Descripción: Geocercas para fichaje por ubicación
-- ============================================================
CREATE TABLE geofences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    name            VARCHAR(100) NOT NULL,   -- "Restaurante Principal", "Cocina Central"
    address         TEXT,
    latitude        NUMERIC(10,7) NOT NULL,
    longitude       NUMERIC(10,7) NOT NULL,
    radius_meters   INTEGER DEFAULT 50,      -- Radio de la geocerca
    is_active       BOOLEAN DEFAULT TRUE,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_geofences_tenant ON geofences(tenant_id);
```

### 1.18 Tabla: `document_templates`

```sql
-- ============================================================
-- TABLE: document_templates
-- Descripción: Plantillas para contratos, nóminas, informes
-- ============================================================
CREATE TABLE document_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    name            VARCHAR(200) NOT NULL,   -- "Contrato Indefinido", "Nómina Mensual"
    type            VARCHAR(50) NOT NULL,    -- contract, payroll, report, settlement
    content         TEXT NOT NULL,            -- HTML / Markdown con variables
    variables       JSONB,                   -- Lista de variables disponibles
    is_default      BOOLEAN DEFAULT FALSE,
    version         INTEGER DEFAULT 1,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.19 Diagrama de Relaciones

```
tenants ──┬── employees
          ├── users
          ├── shifts
          ├── schedules
          ├── clock_ins
          ├── holidays
          ├── work_calendar
          ├── geofences
          ├── document_templates
          ├── notifications
          ├── audit_log
          │
employees ─┬── contracts
           ├── vacation_requests
           ├── leave
           ├── overtime
           ├── payroll
           ├── incidents
           ├── schedules
           ├── clock_ins
           │
shifts ────┬── schedules
           ├── employees (default_shift_id)
           │
holidays ──┬── work_calendar
```

---

## 2. Estructura de Navegación del Dashboard

### 2.1 Menú Lateral Completo

```
┌─────────────────────────────────────────────┐
│  🟧 TalentUP Fichaje                        │ ← Logo + nombre
├─────────────────────────────────────────────┤
│                                             │
│  ◻ Dashboard                                │ ← Home / Resumen
│    ├ Resumen del día                        │
│    ├ Actividad en tiempo real               │
│    └ Alertas / Incidencias                  │
│                                             │
│  ◻ Empleados                               │
│    ├ Listado de empleados                   │
│    ├ Alta de nuevo empleado                │
│    ├ Ficha individual                      │
│    │   ├ Datos personales                  │
│    │   ├ Datos laborales                   │
│    │   ├ Contratos                         │
│    │   ├ Vacaciones                        │
│    │   ├ Bajas / Permisos                  │
│    │   ├ Fichajes                          │
│    │   └ Documentos                        │
│    ├ Importar empleados (CSV/Excel)        │
│    └ Exportar plantilla                    │
│                                             │
│  ◻ Turnos y Horarios                       │
│    ├ Configuración de turnos               │
│    │   ├ Tipos de turno                    │
│    │   ├ Turnos rotativos                  │
│    │   └ Plus de nocturnidad/festividad    │
│    ├ Planificación semanal                │
│    │   ├ Vista calendario                 │
│    │   ├ Vista tabla                       │
│    │   ├ Asignación manual                │
│    │   └ Asignación automática (rotación)  │
│    ├ Calendario laboral                   │
│    │   ├ Festivos nacionales              │
│    │   ├ Festivos autonómicos             │
│    │   ├ Festivos locales                 │
│    │   └ Días especiales                  │
│    └ Plantillas de horario                │
│                                             │
│  ◻ Fichajes                                │
│    ├ Registro de fichajes                 │
│    │   ├ Tiempo real                      │
│    │   ├ Histórico                        │
│    │   └ Por empleado                     │
│    ├ Incidencias de fichaje               │
│    │   ├ Pendientes                       │
│    │   ├ Resueltas                        │
│    │   └ Auto-detectadas                  │
│    ├ Anular fichaje                       │
│    └ Fichaje manual (gestor)              │
│                                             │
│  ◻ Vacaciones y Permisos                  │
│    ├ Solicitudes pendientes               │
│    ├ Calendario de vacaciones             │
│    ├ Saldo de empleados                   │
│    ├ Histórico                            │
│    └ Configuración de permisos            │
│                                             │
│  ◻ Bajas (IT)                              │
│    ├ Bajas activas                        │
│    ├ Histórico de bajas                   │
│    ├ Próximos vencimientos                │
│    └ Estadísticas                         │
│                                             │
│  ◻ Horas Extras                            │
│    ├ Pendientes de compensar              │
│    ├ Histórico                            │
│    └ Informe mensual                      │
│                                             │
│  ◻ Nóminas                                 │
│    ├ Cierre mensual                       │
│    │   ├ Calcular horas                   │
│    │   ├ Revisar incidencias              │
│    │   └ Generar nóminas                  │
│    ├ Histórico de nóminas                 │
│    ├ Finiquitos                           │
│    └ Exportar (SIGMA / ContaSol)          │
│                                             │
│  ◻ Informes                                │
│    ├ Informe diario de fichajes           │
│    ├ Informe mensual de horas             │
│    ├ Informe de horas extras              │
│    ├ Informe de absentismo                │
│    ├ Informe de costes laborales          │
│    ├ Informe de vacaciones                │
│    └ Informe personalizado                │
│                                             │
│  ◻ Notificaciones                         │
│    ├ Bandeja de entrada                   │
│    ├ Histórico                            │
│    └ Configuración de avisos              │
│                                             │
│  ◻ Configuración                          │
│    ├ Datos del establecimiento            │
│    ├ Convenio colectivo                   │
│    ├ Terminales / Tablets                 │
│    ├ Geocercas                            │
│    ├ Roles y permisos                     │
│    ├ Plantillas de documentos             │
│    ├ Integraciones                        │
│    │   ├ SIGMA / ContaSol                │
│    │   ├ Gestor de RRHH externo          │
│    │   └ API pública                     │
│    ├ Facturación / Plan                   │
│    └ Preferencias                         │
│                                             │
├─────────────────────────────────────────────┤
│  👤 Admin                                   │ ← Usuario actual
│  ⚙️ Cerrar sesión                          │
└─────────────────────────────────────────────┘
```

### 2.2 Home / Dashboard Principal

Al abrir la app, el responsable de RRHH ve:

```
┌──────────────────────────────────────────────────────────────┐
│  🟧 TalentUP Fichaje           📅 Hoy, 18 julio 2025        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 👥 12    │  │ ⏱ 8     │  │ ⚠️ 3     │  │ 💰 45h   │    │
│  │ Activos  │  │ Fichados │  │ Inciden. │  │ Extras   │    │
│  │ hoy      │  │ ahora    │  │ pend.    │  │ esta sem │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  📋 Fichajes de hoy                          Ver más │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │  👤 María García     ✅ Entrada   08:02              │    │
│  │  👤 Carlos López     ⏳ Pausa     13:30              │    │
│  │  👤 Ana Martínez     ❌ Sin fichar                   │    │
│  │  👤 Pedro Ruiz       ⚠️ Retraso   08:17 (+17 min)   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐   │
│  │  📅 Próximas ausencias  │  │  ⚠️ Incidencias activas │   │
│  ├─────────────────────────┤  ├─────────────────────────┤   │
│  │  🏖️ Ana → 21-28 jul    │  │  ⚠️ Carlos no fichó     │   │
│  │  🏖️ Pedro → 1-15 ago   │  │  🔴 María retraso 3º   │   │
│  │  🩺 Luis → baja IT      │  │  ⚠️ Juan salió antes   │   │
│  └─────────────────────────┘  └─────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  📊 Horas semanales (progreso)                       │    │
│  │  ─────────────────────────────────────────────       │    │
│  │  María:  ████████████░░░░░░  28h / 40h               │    │
│  │  Carlos: ██████████████░░░░  32h / 40h               │    │
│  │  Ana:    ██████████░░░░░░░░  22h / 40h               │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Accesos Rápidos Necesarios

El dashboard debe tener accesos directos a las acciones más frecuentes:

1. **🔘 Fichar empleado manualmente** (cuando el terminal no funciona)
2. **➕ Añadir empleado rápido** (alta exprés con datos mínimos)
3. **📋 Aprobar vacaciones** (acceso directo a solicitudes pendientes)
4. **⚠️ Resolver incidencias** (acceso a incidencias sin resolver)
5. **📊 Generar informe diario** (para inspección)
6. **📅 Planificar semana** (acceso a horarios de la semana siguiente)
7. **🔍 Buscar empleado** (buscador global por nombre, DNI, categoría)

---

## 3. Flujos de Trabajo Principales

### 3.1 Flujo de Alta de Nuevo Empleado

```
┌─────────────────────────────────────────────────────────────────┐
│  ALTA DE NUEVO EMPLEADO                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PASO 1: DATOS PERSONALES                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Nombre *: ___________  Apellidos *: ________________    │    │
│  │ DNI/NIE: ___________  NSS: ___________________          │    │
│  │ Fecha nac.: ________  Nacionalidad: ___________        │    │
│  │ Teléfono: ___________  Email: __________________       │    │
│  │ Dirección: ___________________________________         │    │
│  │ Contacto emergencia: ___________  Tel: ________        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 2: DATOS LABORALES                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Categoría profesional: [▼ Seleccionar...]               │    │
│  │ Tipo de contrato: [▼ Seleccionar...]                    │    │
│  │ Fecha de alta: ___________  Fecha fin: ___________      │    │
│  │ Tipo de jornada: [▼ Completa | Parcial | Fijo-Disc.]   │    │
│  │ Horas semanales: ___________                            │    │
│  │ Turno habitual: [▼ Seleccionar...]                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 3: DATOS DE FICHAJE                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ PIN (4 dígitos): [____]  Confirmar PIN: [____]          │    │
│  │ Tarjeta NFC: [Leer tarjeta]  o  Introducir ID: _____   │    │
│  │ Foto: [📷 Capturar]  [📁 Subir]                        │    │
│  │ Método fichaje: [▼ PIN | NFC | Huella | Facial]        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 4: DATOS DE VACACIONES Y BANCARIOS                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Días vacaciones/año: 30 (según convenio)                │    │
│  │ IBAN: ____________________  Titular: _____________      │    │
│  │ Banco: _______________                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 5: DOCUMENTACIÓN                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📄 Contrato firmado: [📁 Subir PDF]                    │    │
│  │ 📄 DNI/NIE: [📁 Subir]                                 │    │
│  │ 📄 NSS: [📁 Subir]                                     │    │
│  │ 📄 Cert. manipulación alimentos: [📁 Subir]            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [← Atrás]                              [✅ Dar de alta]       │
│                                                                 │
│  ✅ ALTA COMPLETADA:                                            │
│  • Empleado creado con código EMP-012                         │
│  • PIN asignado: ****                                         │
│  • Contrato registrado                                        │
│  • Notificación enviada al empleado                           │
│  • Opción: [📧 Enviar credenciales] [📄 Imprimir contrato]    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Flujo de Asignación de Turno Semanal

```
┌─────────────────────────────────────────────────────────────────┐
│  ASIGNACIÓN DE TURNOS SEMANALES                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  VISTA: Calendario semanal                          📅 Semana  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         │ Lun 21 │ Mar 22 │ Mié 23 │ Jue 24 │ Vie 25  │    │
│  ├─────────┼────────┼────────┼────────┼────────┼──────────┤    │
│  │ María   │  M     │  M     │  T     │  T     │   N      │    │
│  │ García  │ 07-15  │ 07-15  │ 15-23  │ 15-23  │  23-07   │    │
│  ├─────────┼────────┼────────┼────────┼────────┼──────────┤    │
│  │ Carlos  │  T     │  T     │  M     │  M     │   P      │    │
│  │ López   │ 15-23  │ 15-23  │ 07-15  │ 07-15  │  10-16   │    │
│  ├─────────┼────────┼────────┼────────┼────────┼──────────┤    │
│  │ Ana     │  P     │  P     │  —     │  M     │   M      │    │
│  │ Martínez│ 10-16  │ 10-16  │ DESCANSO│07-15  │  07-15   │    │
│  ├─────────┼────────┼────────┼────────┼────────┼──────────┤    │
│  │ Pedro   │  N     │  N     │  N     │  —     │   T      │    │
│  │ Ruiz    │ 23-07  │ 23-07  │ 23-07  │DESCANSO│  15-23   │    │
│  └─────────┴────────┴────────┴────────┴────────┴──────────┘    │
│                                                                 │
│  ACCIONES:                                                      │
│  [✏️ Editar celda] [📋 Copiar semana anterior]                 │
│  [🔄 Generar rotación automática] [📥 Importar Excel]          │
│  [📤 Publicar horario] → Notifica a todos los empleados        │
│                                                                 │
│  ROTACIÓN AUTOMÁTICA:                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Grupo A: Semana 1→M, Semana 2→T, Semana 3→N, Semana 4→P │    │
│  │ Grupo B: Semana 1→T, Semana 2→N, Semana 3→P, Semana 4→M │    │
│  │ Grupo C: Semana 1→N, Semana 2→P, Semana 3→M, Semana 4→T │    │
│  │ [🔄 Aplicar rotación]                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Flujo de Solicitud/Aprobación de Vacaciones

```
┌─────────────────────────────────────────────────────────────────┐
│  SOLICITUD DE VACACIONES                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EMPLEADO SOLICITA (desde app móvil o web):                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 🏖️ Solicitar vacaciones                                 │    │
│  │                                                         │    │
│  │ Fecha inicio: [21/07/2025]  Fecha fin: [28/07/2025]    │    │
│  │ Días solicitados: 6 (laborables)                        │    │
│  │ Días disponibles: 22                                    │    │
│  │                                                         │    │
│  │ Motivo: ________________________________                │    │
│  │                                                         │    │
│  │ [📨 Enviar solicitud]                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  RRHH RECIBE NOTIFICACIÓN:                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 🔔 Nueva solicitud de vacaciones                        │    │
│  │ 👤 María García solicita 6 días (21-28 jul)            │    │
│  │ 📊 Conflicto: Pedro Ruiz ya tiene vacaciones esas fechas│    │
│  │                                                         │    │
│  │ [✅ Aprobar]  [❌ Rechazar]  [📋 Ver calendario]        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  RRHH REVISA:                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📅 Calendario de vacaciones - Julio 2025               │    │
│  │                                                         │    │
│  │  Lun 21 │ Mar 22 │ Mié 23 │ Jue 24 │ Vie 25 │ Sáb 26  │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│    │
│  │  │María │ │María │ │María │ │María │ │María │ │      ││    │
│  │  │      │ │      │ │      │ │      │ │      │ │      ││    │
│  │  │Pedro │ │Pedro │ │Pedro │ │      │ │      │ │      ││    │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘│    │
│  │                                                         │    │
│  │ ⚠️ Coincidencia con Pedro Ruiz (21-23 jul)             │    │
│  │ ¿Aprobar a pesar de la coincidencia?                   │    │
│  │ [✅ Sí, aprobar]  [❌ No, pedir cambio]                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  RESULTADO:                                                     │
│  • Solicitud aprobada ✅                                       │
│  • Notificación enviada a María García                         │
│  • Calendario actualizado                                      │
│  • Saldo de María: 22 → 16 días disponibles                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Flujo de Registro de Baja IT

```
┌─────────────────────────────────────────────────────────────────┐
│  REGISTRO DE BAJA IT (Incapacidad Temporal)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PASO 1: REGISTRAR BAJA                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 🩺 Nueva baja médica                                    │    │
│  │                                                         │    │
│  │ Empleado: [▼ Buscar...]                                 │    │
│  │ Tipo de baja: [▼ Enfermedad común | Accidente no lab.  │    │
│  │              | Accidente laboral | Enf. profesional     │    │
│  │              | Maternidad | Paternidad]                 │    │
│  │ Fecha inicio: ___________  Fecha fin (prevista): _____  │    │
│  │                                                         │    │
│  │ Datos médicos:                                          │    │
│  │   Diagnóstico: ___________  Código: ________           │    │
│  │   Centro médico: ___________  Médico: ________          │    │
│  │   Nº parte: ___________                                │    │
│  │                                                         │    │
│  │ 📎 Parte de baja: [📁 Subir PDF]                       │    │
│  │                                                         │    │
│  │ [💾 Registrar baja]                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 2: CONSECUENCIAS AUTOMÁTICAS                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ✅ Baja registrada                                      │    │
│  │                                                         │    │
│  │ Acciones automáticas:                                   │    │
│  │ • Estado del empleado → "on_leave"                      │    │
│  │ • Turnos asignados → cancelados (con aviso)             │    │
│  │ • Notificación a RRHH                                   │    │
│  │ • Cálculo de prestación IT iniciado                     │    │
│  │ • Recordatorio de seguimiento en 15 días               │    │
│  │                                                         │    │
│  │ [📧 Notificar a empleado]  [📄 Imprimir parte]          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 3: SEGUIMIENTO                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📋 Bajas activas - Julio 2025                          │    │
│  │                                                         │    │
│  │  👤 Empleado   │ Inicio │ Fin previsto │ Días │ Estado  │    │
│  │  ──────────────┼────────┼──────────────┼──────┼─────────│    │
│  │  Luis Gómez    │ 01-jul │ 15-jul       │ 15   │ 🔴 Venc.│    │
│  │  Ana Ruiz      │ 10-jul │ 30-jul       │ 20   │ 🟡 Activa│    │
│  │                                                         │    │
│  │ ⚠️ Luis Gómez: baja vencida - ¿recibió el alta?        │    │
│  │ [✅ Dar de alta]  [📋 Solicitar prórroga]               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 Flujo de Cierre Mensual (Cálculo de Horas → Nómina)

```
┌─────────────────────────────────────────────────────────────────┐
│  CIERRE MENSUAL                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PASO 1: VERIFICAR DATOS DEL MES                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📊 Cierre mensual - Julio 2025                         │    │
│  │                                                         │    │
│  │ ✅ Todos los empleados tienen fichajes completos        │    │
│  │ ⚠️ 3 empleados con incidencias sin resolver             │    │
│  │ ✅ Calendario laboral actualizado                       │    │
│  │ ✅ Festivos del mes registrados                         │    │
│  │                                                         │    │
│  │ [⚠️ Revisar incidencias]  [✅ Iniciar cálculo]          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 2: CÁLCULO DE HORAS                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ⏱ Horas trabajadas - Julio 2025                       │    │
│  │                                                         │    │
│  │  👤 Empleado   │ Prog.│ Trabaj.│ Extra │ Fest.│ Ausen. │    │
│  │  ──────────────┼──────┼────────┼───────┼──────┼────────│    │
│  │  María García  │ 160h │ 168h   │ 8h    │ 0h   │ 0d     │    │
│  │  Carlos López  │ 160h │ 152h   │ 0h    │ 8h   │ 1d     │    │
│  │  Ana Martínez  │ 120h │ 120h   │ 0h    │ 0h   │ 0d     │    │
│  │  Pedro Ruiz    │ 160h │ 175h   │ 15h   │ 0h   │ 0d     │    │
│  │                                                         │    │
│  │ [📋 Ver detalle]  [✅ Confirmar horas]                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 3: CÁLCULO DE NÓMINA                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 💰 Nóminas - Julio 2025                                │    │
│  │                                                         │    │
│  │  👤 Empleado   │ Bruto   │ Deduc.  │ Neto   │ Estado   │    │
│  │  ──────────────┼─────────┼─────────┼────────┼──────────│    │
│  │  María García  │ 1.850€  │ 385€    │ 1.465€ │ 📝 Borr. │    │
│  │  Carlos López  │ 1.850€  │ 375€    │ 1.475€ │ 📝 Borr. │    │
│  │  Ana Martínez  │ 1.200€  │ 240€    │  960€  │ 📝 Borr. │    │
│  │  Pedro Ruiz    │ 2.100€  │ 440€    │ 1.660€ │ 📝 Borr. │    │
│  │                                                         │    │
│  │ [📄 Vista previa]  [✅ Aprobar todas]                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 4: APROBACIÓN Y EXPORTACIÓN                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ✅ Nóminas aprobadas - Julio 2025                      │    │
│  │                                                         │    │
│  │ Acciones disponibles:                                    │    │
│  │ [📄 Generar PDFs] → Nóminas individuales               │    │
│  │ [📤 Exportar SIGMA] → Fichero para gestoría            │    │
│  │ [📤 Exportar ContaSol] → Fichero para ContaSol          │    │
│  │ [📧 Enviar a empleados] → Cada empleado recibe su nómina│    │
│  │ [📊 Informe de costes] → Resumen para contabilidad      │    │
│  │                                                         │    │
│  │ Total bruto: 7.000€  |  Total neto: 5.560€             │    │
│  │ Total SS empresa: 2.093€ | Total IRPF: 1.120€          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.6 Flujo de Generación de Informe para Inspección

```
┌─────────────────────────────────────────────────────────────────┐
│  INFORME PARA INSPECCIÓN DE TRABAJO                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  REQUISITO LEGAL: RD-ley 8/2019 art. 34.9 ET                   │
│  Conservación: 4 años                                          │
│                                                                 │
│  PASO 1: SELECCIONAR PERIODO                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📋 Informe para inspección                             │    │
│  │                                                         │    │
│  │ Periodo: [01/07/2025] → [18/07/2025]                   │    │
│  │                                                         │    │
│  │ Tipo de informe:                                        │    │
│  │ ○ Completo (todos los empleados)                        │    │
│  │ ○ Por empleado: [▼ Seleccionar...]                      │    │
│  │                                                         │    │
│  │ Incluir:                                                │    │
│  │ ☑️ Registro diario de fichajes                         │    │
│  │ ☑️ Horas trabajadas                                    │    │
│  │ ☑️ Horas extras                                        │    │
│  │ ☑️ Incidencias                                         │    │
│  │ ☐ Anulaciones de fichaje                               │    │
│  │ ☑️ Resumen por empleado                                │    │
│  │                                                         │    │
│  │ [📄 Generar informe]                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PASO 2: VISTA PREVIA                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 📄 INFORME DE REGISTRO DE JORNADA                      │    │
│  │ TalentUP Fichaje - Restaurante El Sabor                 │    │
│  │ CIF: B-12345678  |  Periodo: 01/07/2025 - 18/07/2025   │    │
│  │ Generado: 18/07/2025 10:30h                             │    │
│  │                                                         │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │ 1. REGISTRO DIARIO DE FICHAJES                          │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │                                                         │    │
│  │  Fecha: 18/07/2025                                     │    │
│  │  ┌──────────┬────────┬──────────┬──────────┬────────┐  │    │
│  │  │ Empleado │ DNI    │ Entrada  │ Salida   │ Total  │  │    │
│  │  ├──────────┼────────┼──────────┼──────────┼────────┤  │    │
│  │  │ M. García│12345678A│08:02     │ 16:30    │ 8h 28m │  │    │
│  │  │ C. López │87654321B│08:17     │ 16:45    │ 8h 28m │  │    │
│  │  │ A. Martín│11223344C│—         │ —        │ 0h 0m  │  │    │
│  │  └──────────┴────────┴──────────┴──────────┴────────┘  │    │
│  │                                                         │    │
│  │  ... (todos los días del periodo)                       │    │
│  │                                                         │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │ 2. HORAS EXTRAS                                         │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │  ...                                                    │    │
│  │                                                         │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │ 3. INCIDENCIAS                                          │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │  ...                                                    │    │
│  │                                                         │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │ 4. ANULACIONES                                          │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │  ...                                                    │    │
│  │                                                         │    │
│  │ ─────────────────────────────────────────────────────   │    │
│  │ FIRMA DIGITAL: a3f8c2d1... (hash del documento)         │    │
│  │                                                         │    │
│  │ [📥 Descargar PDF]  [📤 Enviar por email]               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.7 Flujo de Gestión de Incidencias

```
┌─────────────────────────────────────────────────────────────────┐
│  GESTIÓN DE INCIDENCIAS                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DETECCIÓN AUTOMÁTICA (background job diario):                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 🔍 Escaneando fichajes del día...                      │    │
│  │                                                         │    │
│  │ ⚠️ Ana Martínez → No fichó entrada (turno 07:00)       │    │
│  │ ⚠️ Carlos López → Retraso 17 min (tolerancia: 15 min)  │    │
│  │ ⚠️ Pedro Ruiz → Salió 30 min antes del turno           │    │
│  │ ⚠️ María García → No registró pausa (>6h trabajadas)   │    │
│  │                                                         │    │
│  │ [✅ Revisar y gestionar]                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  LISTADO DE INCIDENCIAS:                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ⚠️ Incidencias pendientes (5)                         │    │
│  │                                                         │    │
│  │  Fecha    │ Empleado   │ Tipo          │ Severidad │    │
│  │  ─────────┼────────────┼───────────────┼───────────│    │
│  │  18-jul   │ Ana M.     │ No fichó      │ 🔴 Crítica│    │
│  │  18-jul   │ Carlos L.  │ Retraso       │ 🟡 Media  │    │
│  │  18-jul   │ Pedro R.   │ Salida antes  │ 🟡 Media  │    │
│  │  18-jul   │ María G.   │ Sin pausa     │ 🟢 Leve   │    │
│  │  17-jul   │ Luis G.    │ No fichó      │ 🔴 Crítica│    │
│  │                                                         │    │
│  │ [🔍 Ver detalle]  [✅ Resolver]  [📋 Resolución masiva]│    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  DETALLE Y RESOLUCIÓN:                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ⚠️ Incidencia: No fichó                                │    │
│  │                                                         │    │
│  │ Empleado: Ana Martínez                                  │    │
│  │ Fecha: 18/07/2025                                      │    │
│  │ Turno asignado: Mañana (07:00-15:00)                    │    │
│  │                                                         │    │
│  │ Acción:                                                 │    │
│  │ ○ Empleado olvidó fichar → [📝 Fichaje manual]         │    │
│  │ ○ Empleado ausente sin avisar → [📋 Marcar ausencia]   │    │
│  │ ○ Error del sistema → [✅ Descartar incidencia]         │    │
│  │ ○ Otro: ________________________________               │    │
│  │                                                         │    │
│  │ Nota de resolución: ________________________________    │    │
│  │                                                         │    │
│  │ [💾 Guardar resolución]                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Tipos de Datos del Convenio de Hostelería

### 4.1 Categorías Profesionales

Basadas en el Convenio Colectivo de Hostelería (varía ligeramente por CCAA):

| Código | Categoría | Descripción | Grupo |
|--------|-----------|-------------|-------|
| COC-01 | Jefe de Cocina | Responsable de la cocina | Cocina |
| COC-02 | Segundo Jefe de Cocina | Ayudante del jefe de cocina | Cocina |
| COC-03 | Cocinero | Elaboración de platos | Cocina |
| COC-04 | Ayudante de Cocina | Apoyo en cocina | Cocina |
| COC-05 | Pinche de Cocina | Tareas básicas de cocina | Cocina |
| COC-06 | Repostero | Elaboración de postres y repostería | Cocina |
| COC-07 | Jefe de Partida | Responsable de una sección de cocina | Cocina |
| SAL-01 | Jefe de Sala | Responsable del servicio en sala | Sala |
| SAL-02 | Maître | Jefe de comedor | Sala |
| SAL-03 | Camarero/a | Servicio en mesa | Sala |
| SAL-04 | Ayudante de Camarero | Apoyo en sala | Sala |
| SAL-05 | Sumiller | Especialista en vinos | Sala |
| SAL-06 | Jefe de Rango | Responsable de una zona de sala | Sala |
| BAR-01 | Jefe de Barra | Responsable de la barra | Barra |
| BAR-02 | Camarero de Barra | Servicio en barra | Barra |
| BAR-03 | Ayudante de Barra | Apoyo en barra | Barra |
| BAR-04 | Cafetero | Especialista en café | Barra |
| REC-01 | Recepcionista | Recepción (hoteles) | Recepción |
| REC-02 | Jefe de Recepción | Responsable de recepción | Recepción |
| REC-03 | Conserje | Conserjería | Recepción |
| PIS-01 | Gobernante/a | Responsable de pisos (hoteles) | Pisos |
| PIS-02 | Camarero/a de Pisos | Limpieza de habitaciones | Pisos |
| PIS-03 | Ayudante de Pisos | Apoyo en pisos | Pisos |
| PIS-04 | Lavandero/a | Lavandería y plancha | Pisos |
| ADM-01 | Gerente | Dirección del establecimiento | Administración |
| ADM-02 | Subgerente | Subdirección | Administración |
| ADM-03 | Administrativo | Tareas administrativas | Administración |
| ADM-04 | Auxiliar Administrativo | Apoyo administrativo | Administración |
| ADM-05 | Contable | Gestión contable | Administración |
| MNT-01 | Mantenimiento | Reparaciones y mantenimiento | Mantenimiento |
| MNT-02 | Limpiador/a | Limpieza general | Mantenimiento |
| ALM-01 | Almacenero | Gestión de almacén | Almacén |
| APR-01 | Aprendiz | En formación (menor de 21 años) | Formación |

### 4.2 Tipos de Contrato Válidos

| Código | Tipo de Contrato | Descripción |
|--------|------------------|-------------|
| IND | Indefinido ordinario | Sin fecha de fin |
| IND-FD | Indefinido fijo-discontinuo | Para temporada, con derecho de reincorporación |
| TEM-OC | Temporal por obra o servicio | Para tareas con autonomía y sustantividad |
| TEM-CIR | Temporal circunstancias producción | Incremento puntual de actividad |
| TEM-INT | Temporal por interinidad | Sustitución de empleado con reserva de puesto |
| TEM-FOR | Contrato formativo | En alternancia con formación |
| TEM-PRA | Contrato en prácticas | Para titulados (máx. 2 años) |
| TEM-TEMP | Temporal de temporada | Para campañas estacionales |
| PAR-IND | Indefinido a tiempo parcial | Jornada reducida sin fin de fecha |
| PAR-TEMP | Temporal a tiempo parcial | Jornada reducida con fecha de fin |
| RELEVO | Contrato de relevo | Para jubilación parcial |

### 4.3 Tipos de Turno

| Código | Tipo | Horario típico | Descripción |
|--------|------|----------------|-------------|
| M | Mañana | 07:00 - 15:00 | Turno de mañana |
| T | Tarde | 15:00 - 23:00 | Turno de tarde |
| N | Noche | 23:00 - 07:00 | Turno nocturno (con plus) |
| P | Partido | 10:00 - 16:00 y 20:00 - 23:00 | Turno partido con pausa entre servicios |
| R | Rotativo | Variable | Rotación entre M/T/N según calendario |
| M-T | Mañana-Tarde | 07:00 - 15:00 / 15:00 - 23:00 | Alternancia semanal M/T |
| INT | Intensivo | 08:00 - 15:00 | Jornada continua sin pausa |
| ESP | Especial | Variable | Eventos, banquetes, fines de semana |
| FLEX | Flexible | Variable | Según necesidades del servicio |

**Plus de nocturnidad:** Las horas entre 22:00 y 06:00 tienen un recargo del 25% sobre el salario base (según convenio).

### 4.4 Tipos de Hora Extra

| Código | Tipo | Descripción | Límite legal |
|--------|------|-------------|--------------|
| ESTR | Estructural | Por necesidades del servicio (puntas de actividad, ausencias imprevistas) | 80h/año |
| FM | Fuerza Mayor | Para prevenir o reparar siniestros o daños urgentes | Sin límite |
| COMP | Compensación | Se compensan con descanso en lugar de pago | Acuerdo partes |

**Notas:**
- Las horas extra estructurales no pueden superar 80 horas al año (ET art. 35)
- Se pagan con un recargo mínimo del 75% sobre el salario hora ordinaria (convenio)
- El empleado puede optar entre pago económico o descanso compensatorio
- Las horas extra de fuerza mayor no computan para el límite de 80h

### 4.5 Tipos de Permiso

| Código | Tipo | Días | Descripción |
|--------|------|------|-------------|
| MATRI | Matrimonio | 15 naturales | Contracción de matrimonio |
| PAREJ | Pareja de hecho | 15 naturales | Inscripción como pareja de hecho |
| NACIM | Nacimiento hijo | 2 días (4 si desplazamiento) | Nacimiento de hijo/a |
| FALL1 | Fallecimiento familiar 1er grado | 2 días (4 si desplazamiento) | Cónyuge, padres, hijos |
| FALL2 | Fallecimiento familiar 2º grado | 1 día (2 si desplazamiento) | Abuelos, hermanos, nietos |
| ENF1 | Enfermedad familiar 1er grado | 2 días (4 si desplazamiento) | Hospitalización o intervención |
| ENF2 | Enfermedad familiar 2º grado | 1 día (2 si desplazamiento) | Hospitalización |
| MUDAN | Mudanza | 1 día | Cambio de domicilio habitual |
| EXAM | Examen | 1 día | Exámenes oficiales (justificante) |
| DEBER | Deber inexcusable | Necesario | Votaciones, juicios, etc. |
| SANGRE | Donación sangre | 4 horas | Donación de sangre (justificante) |
| SIND | Funciones sindicales | Necesario | Representación sindical |
| FORMA | Formación | 20h/año | Formación profesional para el empleo |
| MATERN | Maternidad | 16 semanas | Descanso por maternidad |
| PATERN | Paternidad | 16 semanas | Descanso por paternidad |
| LACTAN | Lactancia | 1h/día (o reducción) | Hasta 9 meses del hijo |
| PER-P | Permiso personal | Según política | Permiso no retribuido |
| PER-R | Permiso retribuido | Según convenio | Permiso con sueldo |

### 4.6 Tipos de Incidencia

| Código | Tipo | Severidad | Descripción |
|--------|------|-----------|-------------|
| NO_CLOCK | No fichó entrada | 🔴 Crítica | Empleado con turno asignado que no registró entrada |
| NO_CLOCK_OUT | No fichó salida | 🟡 Media | Empleado que fichó entrada pero no salida |
| LATE | Retraso | 🟡 Media | Fichó después de la hora de inicio (+tolerancia) |
| EARLY_LEAVE | Salida anticipada | 🟡 Media | Fichó salida antes de la hora de fin |
| NO_BREAK | Sin pausa | 🟢 Leve | Trabajó más de 6h sin registrar pausa |
| SHORT_BREAK | Pausa insuficiente | 🟢 Leve | Pausa menor a la mínima establecida |
| EXTRA_HOURS | Horas extra | 🟡 Media | Superó la jornada diaria sin autorización |
| NO_SHOW | Ausente sin avisar | 🔴 Crítica | No se presentó a trabajar |
| INVALID_CLOCK | Fichaje fuera de turno | 🟡 Media | Fichó en horario no asignado |
| GEOFENCE | Fichaje fuera de geocerca | 🟢 Leve | Fichó desde ubicación no autorizada |
| CONSECUTIVE | Días consecutivos sin descanso | 🟡 Media | Superó el máximo de días trabajados seguidos |
| DUPLICATE | Fichaje duplicado | 🟢 Leve | Dos fichajes del mismo tipo muy cercanos |
| OFFLINE | Fichaje offline pendiente | 🟢 Leve | Fichaje realizado sin conexión sin sincronizar |

### 4.7 Tipos de Baja (IT)

| Código | Tipo | Descripción | Duración típica |
|--------|------|-------------|-----------------|
| EC | Enfermedad Común | Enfermedad no relacionada con el trabajo | Variable |
| ANL | Accidente No Laboral | Accidente fuera del trabajo | Variable |
| AL | Accidente Laboral | Accidente durante el trabajo | Variable |
| EP | Enfermedad Profesional | Enfermedad derivada del trabajo | Variable |
| MAT | Maternidad | Descanso por maternidad | 16 semanas |
| PAT | Paternidad | Descanso por paternidad | 16 semanas |
| RIESGO | Riesgo durante embarazo | Suspensión por riesgo en el embarazo | Variable |
| LACT | Lactancia acumulada | Lactancia acumulada en jornada completa | Variable |
| CUID | Cuidado de menor | Reducción por cuidado de menor | Variable |
| FAM | Cuidado familiar | Reducción por cuidado de familiar | Variable |

---

## 5. Reportes que Debe Generar

### 5.1 Informe Diario de Fichajes (para Inspección)

**Propósito:** Cumplimiento legal RD-ley 8/2019. Documento oficial para presentar a la Inspección de Trabajo.

**Contenido:**
- Cabecera: nombre/razón social del establecimiento, CIF, dirección
- Periodo del informe
- Fecha y hora de generación
- Tabla por día con:
  - Nombre y DNI del empleado
  - Hora de entrada
  - Hora de salida
  - Pausas (inicio/fin)
  - Total horas trabajadas
  - Tipo de jornada
- Resumen de horas extras
- Incidencias del periodo
- Anulaciones de fichajes (con motivo)
- Firma digital / hash de integridad

**Formatos:** PDF (con firma digital), Excel, CSV

**Frecuencia:** Diario (generación automática al cierre del día)

### 5.2 Informe Mensual de Horas por Empleado (para Nómina)

**Propósito:** Base de cálculo para la nómina mensual.

**Contenido:**
- Periodo (mes/año)
- Por cada empleado:
  - Datos del empleado (nombre, DNI, categoría, tipo contrato)
  - Horas programadas en el mes
  - Horas realmente trabajadas
  - Desglose por tipo de turno (mañana, tarde, noche, partido)
  - Horas en festivos
  - Horas nocturnas
  - Horas extra (estructurales / fuerza mayor)
  - Ausencias (con tipo: vacaciones, baja IT, permiso)
  - Retrasos (minutos acumulados)
  - Días trabajados
- Totales del establecimiento

**Formatos:** PDF, Excel, CSV (importable a SIGMA/ContaSol)

**Frecuencia:** Mensual (generación al cierre del mes)

### 5.3 Informe de Horas Extras

**Propósito:** Control y compensación de horas extraordinarias.

**Contenido:**
- Periodo seleccionado
- Por empleado:
  - Total horas extra en el periodo
  - Desglose por tipo (estructural / fuerza mayor)
  - Fechas concretas de cada hora extra
  - Importe calculado (con recargo)
  - Estado de compensación (pendiente, pagada, compensada con descanso)
  - Horas extra pendientes de compensar
- Acumulado anual por empleado (control límite 80h)
- Total horas extra del establecimiento
- Coste total de horas extra

**Formatos:** PDF, Excel

**Frecuencia:** Mensual / Bajo demanda

### 5.4 Informe de Absentismo

**Propósito:** Análisis de ausencias laborales.

**Contenido:**
- Periodo seleccionado
- Tasa de absentismo global (%)
- Desglose por tipo de ausencia:
  - Bajas IT (enfermedad común, accidente laboral, enfermedad profesional)
  - Vacaciones
  - Permisos retribuidos
  - Ausencias injustificadas
- Por empleado:
  - Días de ausencia total
  - Desglose por tipo
  - Tasa de absentismo individual
- Comparativa con periodo anterior
- Coste estimado del absentismo
- Top 5 empleados con mayor absentismo

**Formatos:** PDF, Excel, gráficos

**Frecuencia:** Mensual / Trimestral

### 5.5 Informe de Costes Laborales

**Propósito:** Control de costes de personal para dirección/contabilidad.

**Contenido:**
- Periodo seleccionado
- Coste total de personal
- Desglose por concepto:
  - Salarios base
  - Complementos (nocturnidad, festividad, antigüedad, etc.)
  - Horas extra
  - Seguridad Social (empresa)
  - Otros costes
- Coste por empleado (individual)
- Coste por hora trabajada
- Coste por categoría profesional
- Comparativa mes anterior / mismo mes año anterior
- Proyección de costes
- % de coste laboral sobre facturación (si se proporciona)

**Formatos:** PDF, Excel

**Frecuencia:** Mensual

### 5.6 Informe de Vacaciones

**Propósito:** Planificación y control de vacaciones.

**Contenido:**
- Año seleccionado
- Calendario visual de vacaciones (por meses)
- Por empleado:
  - Días totales del año
  - Días disfrutados
  - Días pendientes
  - Periodos solicitados (aprobados/pendientes)
- Empleados con más días pendientes
- Empleados con menos días pendientes
- Solapamientos / conflictos detectados
- Previsión de vacaciones para próximos meses
- Alertas: empleados que no han solicitado vacaciones, empleados que superan el máximo acumulado

**Formatos:** PDF, Excel, vista calendario interactiva

**Frecuencia:** Trimestral / Bajo demanda

### 5.7 Informe Personalizado

**Propósito:** Flexibilidad para crear reportes a medida.

**Características:**
- Selección de periodo
- Selección de empleados (todos / grupo / individual)
- Selección de métricas a incluir
- Selección de formato (PDF, Excel, CSV)
- Posibilidad de programar generación automática
- Posibilidad de enviar por email automáticamente

---

## 6. Reglas de Negocio Transversales

### 6.1 Cálculo de Horas Trabajadas

```
Para cada empleado y día:
  1. Obtener todos los clock_ins del día, ordenados por timestamp
  2. Agrupar por tipo:
     - El primer "in" del día marca el inicio de la jornada
     - El último "out" del día marca el fin de la jornada
     - Los "break_start"/"break_end" intermedios son pausas
  3. Si hay múltiples "in"/"out" (turno partido), se suman los segmentos
  4. Horas trabajadas = (último out - primer in) - pausas
  5. Si no hay "out", se considera que sigue trabajando (jornada abierta)
  6. Si no hay "in", se genera incidencia "no_clock_in"
```

### 6.2 Detección de Incidencias (Background Job)

```
Ejecución diaria (cada hora en horario laboral, cierre a las 23:59):
  1. Para cada empleado con turno asignado hoy:
     - ¿Tiene clock_in "in"? → No → Incidencia NO_CLOCK
     - ¿Tiene clock_in "out"? → No → Incidencia NO_CLOCK_OUT
     - ¿Hora del "in" > (hora_inicio_turno + tolerancia)? → Incidencia LATE
     - ¿Hora del "out" < (hora_fin_turno - tolerancia)? → Incidencia EARLY_LEAVE
     - ¿Trabajó > 6h sin break? → Incidencia NO_BREAK
     - ¿Horas trabajadas > horas_turno + umbral_extra? → Incidencia EXTRA_HOURS
  2. Para cada empleado:
     - ¿Lleva > 7 días consecutivos trabajados? → Incidencia CONSECUTIVE
  3. Para cada clock_in offline:
     - ¿Lleva > 24h sin sincronizar? → Incidencia OFFLINE
```

### 6.3 Cálculo de Nómina Mensual

```
Para cada empleado en el mes:
  1. Obtener todas las horas trabajadas del mes (de clock_ins)
  2. Obtener todas las horas extra del mes (de overtime)
  3. Obtener ausencias (vacaciones, bajas, permisos)
  4. Calcular:
     - Horas ordinarias = horas_trabajadas - horas_extra
     - Salario base = (horas_ordinarias / horas_mensuales_contrato) * salario_base_mensual
     - Plus nocturnidad = horas_nocturnas * porcentaje_nocturnidad * hora_base
     - Plus festividad = horas_festivas * porcentaje_festividad * hora_base
     - Plus antigüedad = salario_base * porcentaje_antigüedad (por trienio)
     - Horas extra = horas_extra * hora_base * multiplicador (1.75)
     - Total bruto = suma de todos los conceptos
     - SS empleado = total_bruto * porcentaje_ss_empleado
     - IRPF = total_bruto * porcentaje_irpf (según tramo)
     - Total neto = total_bruto - ss_empleado - irpf
```

### 6.4 Control de Jornada (Límites Legales)

```
- Jornada diaria máxima: 9 horas (ordinaria, puede superarse con horas extra)
- Descanso semanal mínimo: 1.5 días ininterrumpidos (36h)
- Descanso intrajornada: 15 min si jornada > 6h (o 30 min si > 6h continuas)
- Horas extra máximas: 80 horas/año (estructurales)
- Horas extra fuerza mayor: sin límite, pero no computan para las 80h
- Periodo de referencia para jornada: anual (cómputo global)
- Registro obligatorio: TODOS los fichajes, conservación 4 años
```

### 6.5 Cálculo de Vacaciones

```
- Días por año: 30 días naturales (o 22 laborables, según convenio)
- Periodo de devengo: por año natural (o desde fecha de alta)
- Solicitud: mínimo 15 días de antelación (configurable)
- Fraccionamiento: máximo 2 periodos al año (configurable)
- Solapamiento: no más de X empleados de la misma categoría de vacaciones
- Caducidad: las vacaciones deben disfrutarse antes del 31 de diciembre
  (o antes del 31 de marzo del año siguiente, según convenio)
```

---

## 7. API Endpoints (Blueprint)

### 7.1 Autenticación

```
POST   /api/v1/auth/login              → Login (email + password)
POST   /api/v1/auth/register           → Registro (super_admin only)
POST   /api/v1/auth/refresh            → Refresh token
POST   /api/v1/auth/logout             → Logout
POST   /api/v1/auth/forgot-password    → Solicitar reset
POST   /api/v1/auth/reset-password     → Resetear contraseña
GET    /api/v1/auth/me                 → Perfil del usuario actual
PUT    /api/v1/auth/me                 → Actualizar perfil
```

### 7.2 Tenants

```
GET    /api/v1/tenants                 → Listar tenants (super_admin)
POST   /api/v1/tenants                → Crear tenant (super_admin)
GET    /api/v1/tenants/:id            → Detalle tenant
PUT    /api/v1/tenants/:id            → Actualizar tenant
DELETE /api/v1/tenants/:id            → Desactivar tenant
```

### 7.3 Usuarios

```
GET    /api/v1/users                   → Listar usuarios del tenant
POST   /api/v1/users                  → Crear usuario (invitar)
GET    /api/v1/users/:id              → Detalle usuario
PUT    /api/v1/users/:id              → Actualizar usuario
DELETE /api/v1/users/:id              → Desactivar usuario
PUT    /api/v1/users/:id/permissions  → Actualizar permisos
```

### 7.4 Empleados

```
GET    /api/v1/employees              → Listar empleados (filtros: status, category, search)
POST   /api/v1/employees              → Crear empleado
POST   /api/v1/employees/import       → Importar empleados (CSV/Excel)
GET    /api/v1/employees/export-template → Descargar plantilla importación
GET    /api/v1/employees/:id          → Detalle empleado (todos los datos)
PUT    /api/v1/employees/:id          → Actualizar empleado
PATCH  /api/v1/employees/:id/status   → Cambiar estado (active, inactive, etc.)
DELETE /api/v1/employees/:id          → Baja lógica del empleado
GET    /api/v1/employees/:id/contracts → Contratos del empleado
GET    /api/v1/employees/:id/vacations → Vacaciones del empleado
GET    /api/v1/employees/:id/leave    → Bajas del empleado
GET    /api/v1/employees/:id/overtime → Horas extra del empleado
GET    /api/v1/employees/:id/clock-ins → Fichajes del empleado
GET    /api/v1/employees/:id/payroll  → Nóminas del empleado
```

### 7.5 Contratos

```
GET    /api/v1/contracts              → Listar contratos
POST   /api/v1/contracts             → Crear contrato
GET    /api/v1/contracts/:id          → Detalle contrato
PUT    /api/v1/contracts/:id          → Actualizar contrato
POST   /api/v1/contracts/:id/renew    → Renovar contrato
DELETE /api/v1/contracts/:id         → Eliminar contrato
```

### 7.6 Turnos (Shifts)

```
GET    /api/v1/shifts                 → Listar turnos
POST   /api/v1/shifts                → Crear turno
GET    /api/v1/shifts/:id             → Detalle turno
PUT    /api/v1/shifts/:id             → Actualizar turno
DELETE /api/v1/shifts/:id             → Eliminar turno
```

### 7.7 Horarios (Schedules)

```
GET    /api/v1/schedules              → Listar horarios (filtros: week, employee, date)
POST   /api/v1/schedules              → Asignar turno a empleado
POST   /api/v1/schedules/batch        → Asignación masiva
POST   /api/v1/schedules/rotate       → Generar rotación automática
POST   /api/v1/schedules/copy-week    → Copiar semana anterior
PUT    /api/v1/schedules/:id          → Actualizar asignación
DELETE /api/v1/schedules/:id          → Eliminar asignación
POST   /api/v1/schedules/publish      → Publicar horarios (notificar empleados)
GET    /api/v1/schedules/week/:date   → Horarios de la semana
GET    /api/v1/schedules/employee/:id → Horarios de un empleado
```

### 7.8 Fichajes (Clock)

```
POST   /api/v1/clock                  → Fichar (PIN + type + opcional: NFC, ubicación)
POST   /api/v1/clock/offline          → Sincronizar fichajes offline (batch)
GET    /api/v1/clock/history          → Histórico de fichajes (filtros)
GET    /api/v1/clock/today            → Fichajes de hoy
GET    /api/v1/clock/active           → Empleados fichados ahora
POST   /api/v1/clock/:id/cancel       → Anular fichaje (con motivo)
POST   /api/v1/clock/manual           → Fichaje manual (gestor, para empleado)
```

### 7.9 Vacaciones

```
GET    /api/v1/vacations              → Listar solicitudes (filtros: status, employee, dates)
POST   /api/v1/vacations             → Crear solicitud
GET    /api/v1/vacations/:id          → Detalle solicitud
PUT    /api/v1/vacations/:id          → Actualizar solicitud
POST   /api/v1/vacations/:id/approve  → Aprobar solicitud
POST   /api/v1/vacations/:id/reject   → Rechazar solicitud
DELETE /api/v1/vacations/:id          → Cancelar solicitud
GET    /api/v1/vacations/calendar     → Calendario de vacaciones
GET    /api/v1/vacations/balance      → Saldo de vacaciones de todos los empleados
```

### 7.10 Bajas (Leave)

```
GET    /api/v1/leave                  → Listar bajas (filtros: status, type, dates)
POST   /api/v1/leave                 → Registrar baja
GET    /api/v1/leave/:id             → Detalle baja
PUT    /api/v1/leave/:id             → Actualizar baja
POST   /api/v1/leave/:id/extend      → Prórroga de baja
POST   /api/v1/leave/:id/close       → Cerrar baja (alta médica)
GET    /api/v1/leave/active          → Bajas activas
GET    /api/v1/leave/expiring        → Bajas próximas a vencer
```

### 7.11 Horas Extras

```
GET    /api/v1/overtime              → Listar horas extra (filtros: employee, date, status)
POST   /api/v1/overtime             → Registrar hora extra manual
GET    /api/v1/overtime/:id         → Detalle
PUT    /api/v1/overtime/:id         → Actualizar
POST   /api/v1/overtime/:id/approve → Aprobar
POST   /api/v1/overtime/:id/compensate → Compensar (pago o descanso)
GET    /api/v1/overtime/pending     → Pendientes de compensar
GET    /api/v1/overtime/annual-summary → Resumen anual por empleado
```

### 7.12 Nóminas (Payroll)

```
GET    /api/v1/payroll               → Listar nóminas (filtros: year, month, employee)
POST   /api/v1/payroll/calculate     → Calcular nóminas del mes (batch)
GET    /api/v1/payroll/:id           → Detalle nómina
PUT    /api/v1/payroll/:id           → Ajustar nómina manualmente
POST   /api/v1/payroll/:id/approve   → Aprobar nómina
POST   /api/v1/payroll/:id/pay       → Marcar como pagada
POST   /api/v1/payroll/:id/generate-pdf → Generar PDF de nómina
POST   /api/v1/payroll/export/sigma  → Exportar a SIGMA
POST   /api/v1/payroll/export/contasol → Exportar a ContaSol
GET    /api/v1/payroll/summary       → Resumen de costes del periodo
```

### 7.13 Incidencias

```
GET    /api/v1/incidents             → Listar incidencias (filtros: status, type, severity)
GET    /api/v1/incidents/:id         → Detalle incidencia
PUT    /api/v1/incidents/:id         → Actualizar incidencia
POST   /api/v1/incidents/:id/resolve → Resolver incidencia
POST   /api/v1/incidents/:id/dismiss → Descartar incidencia
POST   /api/v1/incidents/manual      → Crear incidencia manual
GET    /api/v1/incidents/stats       → Estadísticas de incidencias
```

### 7.14 Calendario Laboral

```
GET    /api/v1/calendar              → Obtener calendario (año)
POST   /api/v1/calendar/generate     → Generar calendario anual
PUT    /api/v1/calendar/:id           → Actualizar día del calendario
POST   /api/v1/calendar/holidays     → Importar festivos (nacionales, autonómicos, locales)
GET    /api/v1/calendar/holidays     → Listar festivos
POST   /api/v1/calendar/holidays     → Añadir festivo manual
DELETE /api/v1/calendar/holidays/:id → Eliminar festivo
```

### 7.15 Notificaciones

```
GET    /api/v1/notifications         → Listar notificaciones del usuario
GET    /api/v1/notifications/unread  → No leídas
POST   /api/v1/notifications/:id/read → Marcar como leída
POST   /api/v1/notifications/read-all → Marcar todas como leídas
POST   /api/v1/notifications/:id/dismiss → Descartar
GET    /api/v1/notifications/settings → Configuración de notificaciones
PUT    /api/v1/notifications/settings → Actualizar configuración
```

### 7.16 Geocercas

```
GET    /api/v1/geofences             → Listar geocercas
POST   /api/v1/geofences            → Crear geocerca
PUT    /api/v1/geofences/:id        → Actualizar geocerca
DELETE /api/v1/geofences/:id        → Eliminar geocerca
```

### 7.17 Informes / Reportes

```
POST   /api/v1/reports/daily         → Informe diario de fichajes (PDF)
POST   /api/v1/reports/monthly-hours → Informe mensual de horas (PDF/Excel)
POST   /api/v1/reports/overtime      → Informe de horas extra (PDF/Excel)
POST   /api/v1/reports/absenteeism   → Informe de absentismo (PDF/Excel)
POST   /api/v1/reports/labor-costs   → Informe de costes laborales (PDF/Excel)
POST   /api/v1/reports/vacations     → Informe de vacaciones (PDF/Excel)
POST   /api/v1/reports/custom        → Informe personalizado
GET    /api/v1/reports/scheduled     → Informes programados
POST   /api/v1/reports/scheduled     → Programar informe recurrente
DELETE /api/v1/reports/scheduled/:id → Eliminar programación
```

### 7.18 Configuración

```
GET    /api/v1/settings              → Obtener configuración del tenant
PUT    /api/v1/settings              → Actualizar configuración
GET    /api/v1/settings/convenio     → Obtener configuración del convenio
PUT    /api/v1/settings/convenio     → Actualizar configuración del convenio
GET    /api/v1/settings/templates    → Listar plantillas de documentos
POST   /api/v1/settings/templates   → Crear plantilla
PUT    /api/v1/settings/templates/:id → Actualizar plantilla
DELETE /api/v1/settings/templates/:id → Eliminar plantilla
```

### 7.19 Auditoría

```
GET    /api/v1/audit-log             → Listar logs de auditoría (filtros)
GET    /api/v1/audit-log/employee/:id → Auditoría de un empleado
GET    /api/v1/audit-log/export      → Exportar log de auditoría
```

### 7.20 Terminal / Tablet

```
GET    /api/v1/terminal/config       → Obtener configuración del terminal
POST   /api/v1/terminal/register    → Registrar terminal
POST   /api/v1/terminal/heartbeat   → Heartbeat del terminal
GET    /api/v1/terminal/employees    → Lista de empleados para el terminal (PIN + foto)
POST   /api/v1/terminal/clock       → Fichar desde terminal
POST   /api/v1/terminal/sync        → Sincronizar fichajes offline
```

---

## Apéndice A: Migración desde la Versión Actual

La app actual tiene estos modelos:
- `employees` (mínimo: solo name, dni, pin_hash, nfc_card_id, photo_url, shift_id, is_active)
- `shifts` (básico: name, start_time, end_time, tolerance, is_split, break_min)
- `schedules` (básico: employee_id, shift_id, date, notes)
- `clock_ins` (básico: type, timestamp, lat/lng, is_offline, is_cancelled)
- `incidents` (básico: type, description, severity, is_resolved)
- `tenants` (básico: name, legal_name, cif, address, convenio, tolerancia)
- `users` (básico: email, password_hash, name, role)
- `audit_log` (básico: action, entity_type, entity_id, old/new_value)

**Migración necesaria:**
1. Añadir ~30 columnas a `employees` (ver sección 1.1)
2. Crear tablas nuevas: `contracts`, `holidays`, `vacation_requests`, `leave`, `overtime`, `payroll`, `notifications`, `work_calendar`, `geofences`, `document_templates`
3. Ampliar `tenants` con ~20 columnas de configuración
4. Ampliar `users` con permisos granulares y 2FA
5. Migrar datos existentes a la nueva estructura

---

## Apéndice B: Stack Técnico Recomendado

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| **Backend** | FastAPI (Python 3.11+) | Rendimiento, tipado, documentación automática |
| **Base de datos** | PostgreSQL 15+ | JSONB para flexibilidad, índices avanzados, integridad referencial |
| **ORM** | SQLAlchemy 2.0 + Alembic | Migraciones, async support |
| **Frontend gestor** | React 18 + Vite + TailwindCSS | Rendimiento, ecosistema, UI consistente |
| **Frontend terminal** | React PWA (offline-first) | Funciona sin conexión, kiosk-mode |
| **Auth** | JWT + refresh tokens + 2FA | Seguridad, stateless |
| **Background jobs** | Celery + Redis | Cálculos nocturnos, detección de incidencias, notificaciones |
| **PDF generation** | WeasyPrint / ReportLab | Documentos legales con formato |
| **Exportación** | OpenPyXL (Excel), CSV | Compatibilidad con gestorías |
| **Almacenamiento** | S3-compatible (fotos, documentos) | Escalable, económico |
| **Infraestructura** | Docker + Vercel/Railway/Neon | Despliegue sencillo, escalable |

---

> **Documento generado como blueprint completo para reconstruir TalentUP Fichaje como SaaS comercializable de fichaje digital para hostelería.**
>
> Versión: 2.0 · Fecha: Julio 2025
