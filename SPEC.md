# TalentUP Fichaje — Spec de Producto

## Concepto
SaaS de fichaje digital para hostelería con terminal físico (tablet). Cumple RD-ley 8/2019 art. 34.9 ET.

## Multi-tenant
Cada restaurante es un tenant aislado. Un admin de Grupo RAS ve todos los tenants.

## Roles
- **Super Admin** (Grupo RAS): gestiona todos los restaurantes, crea tenants
- **Owner** (dueño restaurante): gestiona su restaurante, empleados, turnos
- **Manager** (encargado): ficha, ve informes de su turno
- **Employee** (empleado): solo ficha entrada/salida/pausa

## Features MVP (obligatorias para vender)

### Terminal (tablet en pared, kiosk-mode)
1. Pantalla inicial: "Introduce tu PIN" (teclado numérico grande)
2. Tras PIN válido: muestra nombre + foto del empleado
3. Botones: ENTRAR | SALIR | PAUSA INICIO | PAUSA FIN
4. Confirmación visual + sonido (bip OK / bip error)
5. Muestra hora actual grande
6. Funciona offline (sync cuando hay conexión)
7. No se puede salir sin PIN de admin

### Dashboard gestor (web)
1. **Resumen**: empleados activos hoy, fichajes pendientes, incidencias
2. **Empleados**: CRUD completo (nombre, DNI, PIN, turno, foto)
3. **Fichajes**: listado con filtros (fecha, empleado, tipo)
4. **Turnos**: crear/editar turnos (mañana, tarde, noche, partido)
5. **Horarios**: asignar turnos a empleados por día/semana
6. **Informes**: 
   - Horas trabajadas por empleado (día/semana/mes)
   - Horas extras calculadas
   - Incidencias (no fichó, fichó tarde, fichó fuera de turno)
   - Exportar PDF (para inspección) y Excel
7. **Configuración**: datos del restaurante, convenio aplicable, tolerancia fichaje

### Cumplimiento legal
- Registro: fecha, hora inicio, hora fin, ID empleado, tipo (entrada/salida/pausa)
- Conservación 4 años
- Exportación PDF con firma digital del registro
- Registro inmutable (no se puede editar, solo anular con motivo)
- Log de auditoría de todos los cambios

### Multi-tenant
- Cada restaurante aislado (schema o tenant_id)
- Super admin ve todos
- Billing por establecimiento (no por empleado)

## Stack técnico
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend gestor**: React + Vite + TailwindCSS
- **Terminal tablet**: React PWA (offline-first, kiosk-mode)
- **Auth**: JWT con roles + tenant_id
- **Deploy**: Vercel (frontend) + Railway (backend) + Neon (DB)

## Pricing
- Pago único: ~245€ (terminal físico: tablet + soporte + NFC)
- Suscripción: 29-39€/mes por establecimiento (sin límite de empleados)

## Modelo de datos (tablas core)
- tenants (restaurantes)
- users (super_admin, owner, manager, employee)
- employees (datos del empleado, PIN hash, NFC, foto, turno)
- shifts (turnos: nombre, hora inicio, hora fin, tolerancia)
- schedules (asignación empleado-turno-fecha)
- clock_ins (fichajes: employee_id, timestamp, type, tenant_id)
- incidents (incidencias: tipo, descripción, auto-generadas)
- audit_log (cambios en el sistema)

## API endpoints (core)
- POST /api/auth/login
- POST /api/auth/register (super_admin only)
- GET/POST/PUT/DELETE /api/employees
- GET/POST /api/shifts
- GET/POST /api/schedules
- POST /api/clock (fichar: PIN + type)
- GET /api/clock/history
- GET /api/reports/hours
- GET /api/reports/incidents
- GET /api/reports/export (PDF/Excel)