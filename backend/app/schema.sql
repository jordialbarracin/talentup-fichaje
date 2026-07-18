-- TalentUP Fichaje — Schema inicial
-- Multi-tenant SaaS de fichaje digital para hostelería

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tenants (restaurantes)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    legal_name VARCHAR(200),
    cif VARCHAR(20),
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    convenio VARCHAR(100) DEFAULT 'hosteleria',
    tolerancia_min INT DEFAULT 5,
    plan VARCHAR(20) DEFAULT 'basic',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users (super_admin, owner, manager)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(200) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    name VARCHAR(200) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'owner', -- super_admin, owner, manager
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Employees (trabajadores que fichan)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    dni VARCHAR(20),
    pin_hash VARCHAR(200) NOT NULL,
    nfc_card_id VARCHAR(100),
    photo_url TEXT,
    shift_id UUID REFERENCES shifts(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Shifts (turnos)
CREATE TABLE shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    tolerance_min INT DEFAULT 5,
    is_split BOOLEAN DEFAULT FALSE, -- turno partido
    break_min INT DEFAULT 0,
    color VARCHAR(7) DEFAULT '#FF6B35',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Schedules (asignación empleado-turno-fecha)
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    shift_id UUID REFERENCES shifts(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, employee_id, date)
);

-- Clock-ins (fichajes)
CREATE TABLE clock_ins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL, -- in, out, break_start, break_end
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    latitude FLOAT,
    longitude FLOAT,
    is_offline BOOLEAN DEFAULT FALSE,
    synced_at TIMESTAMPTZ,
    is_cancelled BOOLEAN DEFAULT FALSE,
    cancel_reason TEXT,
    cancelled_by UUID REFERENCES users(id),
    cancelled_at TIMESTAMPTZ
);

-- Incidents (incidencias auto-detectadas)
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    type VARCHAR(50) NOT NULL, -- no_clock_in, late, early_leave, no_break, extra_hours
    description TEXT,
    severity VARCHAR(20) DEFAULT 'warning',
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_clock_ins_tenant_date ON clock_ins(tenant_id, timestamp);
CREATE INDEX idx_clock_ins_employee ON clock_ins(employee_id, timestamp);
CREATE INDEX idx_employees_tenant ON employees(tenant_id);
CREATE INDEX idx_incidents_tenant_date ON incidents(tenant_id, date);
CREATE INDEX idx_schedules_tenant_date ON schedules(tenant_id, date);