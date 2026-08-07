"""
TalentUP Fichaje — OpenAPI documentation helpers.

This module centralizes all OpenAPI/Swagger metadata for the API:
  * API title, description, version, contact and license.
  * Tag definitions used to group endpoints by domain in the Swagger UI.
  * Reusable Pydantic response models that describe the shape of endpoints
    which currently return plain ``dict`` objects, so that the generated
    OpenAPI schema is accurate without changing any endpoint logic.

All models defined here are *permissive* (``model_config = ConfigDict(extra="allow")``)
and use ``Optional`` fields with sensible defaults.  This guarantees that adding
``response_model`` to an existing endpoint never filters out fields that the
endpoint already returns — it only enriches the documentation layer.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────────────
# OpenAPI metadata
# ─────────────────────────────────────────────────────────────────────────────
API_TITLE = "TalentUP Fichaje API"
API_DESCRIPTION = (
    "SaaS de fichaje digital para hostelería. Multi-tenant. Cumple RD-ley 8/2019.\n\n"
    "La API gestiona autenticación (JWT + httpOnly cookies), empleados, turnos, "
    "horarios, fichajes (PIN/NFC/QR), incidencias, vacaciones, bajas, horas extra, "
    "nóminas, calendario laboral, notificaciones, informes para Inspección de "
    "Trabajo y facturación vía Stripe.\n\n"
    "**Autenticación:** la mayoría de endpoints requieren un JWT enviado como "
    "`Authorization: Bearer <token>` o mediante la cookie httpOnly `access_token`. "
    "Los endpoints de fichaje (`/api/clock*`) son públicos y se autentican con "
    "PIN/NFC/QR o un device token."
)
API_VERSION = "2.0.0"

API_CONTACT = {
    "name": "TalentUP Fichaje — Soporte",
    "url": "https://talentup-fichaje.com/soporte",
    "email": "soporte@talentup-fichaje.com",
}

API_LICENSE = {
    "name": "Propietario — TalentUP Fichaje",
    "url": "https://talentup-fichaje.com/licencia",
}


# ─────────────────────────────────────────────────────────────────────────────
# Tag definitions — group endpoints by domain in the Swagger UI
# ─────────────────────────────────────────────────────────────────────────────
TAGS_METADATA = [
    {
        "name": "Auth",
        "description": "Autenticación y autorización: login, registro, refresh, logout y perfil del usuario actual.",
    },
    {
        "name": "Employees",
        "description": "Gestión de empleados: alta, edición, baja, búsqueda y consulta de saldos (vacaciones, horas).",
    },
    {
        "name": "Scheduling",
        "description": "Planificación: turnos (shifts), horarios (schedules), calendario laboral, festivos y vacaciones.",
    },
    {
        "name": "Clock",
        "description": (
            "Fichaje digital: entrada/salida/pausa mediante PIN, NFC o QR. "
            "Incluye historial, fichajes del día, anulación y WebSocket en tiempo real para lectores NFC. "
            "Estos endpoints son públicos (sin JWT) y se autentican con PIN/NFC/QR o device token."
        ),
    },
    {
        "name": "Reports",
        "description": (
            "Informes: horas trabajadas, incidencias, exportación a PDF/Excel, informe para Inspección "
            "de Trabajo (RD-ley 8/2019), absentismo y costes laborales."
        ),
    },
    {
        "name": "Admin",
        "description": (
            "Administración de tenants (multi-tenant), contratos laborales, dispositivos/terminales, "
            "ajustes del tenant y bajas IT (leave). Acceso restringido a owner/super_admin."
        ),
    },
    {
        "name": "Payroll",
        "description": "Nóminas: listado, consulta por mes/año y cierre (procesamiento en segundo plano).",
    },
    {
        "name": "Notifications",
        "description": "Notificaciones in-app: listado, creación, envío, marcar como leído y contador de no leídas.",
    },
    {
        "name": "Billing",
        "description": "Facturación vía Stripe: checkout sessions, webhooks, estado de suscripción y portal de cliente.",
    },
    {
        "name": "Health",
        "description": "Health check profundo (DB + Redis + uptime) y métricas Prometheus.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Reusable error response schemas
# ─────────────────────────────────────────────────────────────────────────────
class ErrorResponse(BaseModel):
    """Standard error envelope returned by all endpoints on failure."""

    model_config = ConfigDict(extra="allow")
    detail: Any = Field(..., description="Descripción del error en español.")


class ValidationError(BaseModel):
    """Pydantic/FastAPI 422 validation error envelope."""

    model_config = ConfigDict(extra="allow")
    detail: List[Dict[str, Any]] = Field(
        ..., description="Lista de errores de validación campo a campo."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Generic paginated response
# ─────────────────────────────────────────────────────────────────────────────
class PageResponse(BaseModel):
    """Standard paginated envelope returned by list endpoints: ``{items, total, page, limit, pages}``."""

    model_config = ConfigDict(extra="allow")
    items: List[Dict[str, Any]] = Field(..., description="Página actual de resultados.")
    total: int = Field(..., description="Número total de resultados que coinciden con el filtro.")
    page: int = Field(..., description="Página actual (1-based).")
    limit: int = Field(..., description="Resultados por página.")
    pages: int = Field(..., description="Número total de páginas.")


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    """User profile as returned by ``GET /api/auth/me`` and inside auth responses."""

    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = Field(None, description="Rol: owner, manager, employee o super_admin.")
    tenant_id: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None


class AuthResponse(BaseModel):
    """Login/register success response. JWT tokens are also set as httpOnly cookies."""

    model_config = ConfigDict(extra="allow")
    ok: bool = Field(True, description="Indica si la autenticación fue exitosa.")
    user: Dict[str, Any] = Field(..., description="Datos del usuario autenticado.")
    tenant_id: Optional[str] = Field(None, description="ID del tenant al que pertenece el usuario.")
    is_new_tenant: bool = Field(False, description="True cuando se acaba de crear un nuevo tenant (registro).")


class LogoutResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    ok: bool = True
    message: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Clock
# ─────────────────────────────────────────────────────────────────────────────
class ClockRecord(BaseModel):
    """A single clock-in entry (entrada/salida/pausa)."""

    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    employee_id: Optional[str] = None
    type: Optional[str] = Field(None, description="Tipo de fichaje: in, out, break_start, break_end.")
    timestamp: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_offline: Optional[bool] = None
    is_cancelled: Optional[bool] = None


class ClockResponse(BaseModel):
    """Response from clock-in endpoints (PIN/NFC/QR). Includes the created record."""

    model_config = ConfigDict(extra="allow")
    ok: bool = Field(True, description="Indica si el fichaje se registró correctamente.")
    message: Optional[str] = Field(None, description="Mensaje legible en español (ej: 'Carlos — Entrada registrada').")
    type: Optional[str] = Field(None, description="Tipo de fichaje registrado: in, out, break_start, break_end.")
    employee_name: Optional[str] = None
    time: Optional[str] = Field(None, description="Timestamp ISO 8601 del fichaje.")
    clock: Optional[Dict[str, Any]] = Field(None, description="Registro de fichaje completo.")


class TenantPublicOut(BaseModel):
    """Minimal tenant info for the public PWA endpoint."""

    model_config = ConfigDict(extra="allow")
    id: str
    name: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Employees
# ─────────────────────────────────────────────────────────────────────────────
class EmployeeOut(BaseModel):
    """Employee record (PII masked by default; full PII only with ?full=true for super_admin)."""

    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    dni: Optional[str] = Field(None, description="DNI enmascarado salvo ?full=true.")
    nie: Optional[str] = None
    numero_ss: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    estado: Optional[str] = Field(None, description="activo, baja, vacaciones, permiso.")
    is_active: Optional[bool] = None
    clock_method: Optional[str] = Field(None, description="pin, nfc, qr, fingerprint.")
    nfc_uid: Optional[str] = None
    shift_id: Optional[str] = None
    categoria_profesional: Optional[str] = None
    tipo_contrato: Optional[str] = None
    tipo_jornada: Optional[str] = None
    horas_semanales: Optional[float] = None
    horas_diarias: Optional[float] = None
    vacation_annual_days: Optional[float] = None
    saldo_vacaciones: Optional[float] = None
    saldo_banco_horas: Optional[float] = None
    horas_extra_pendientes: Optional[float] = None
    coste_hora: Optional[float] = None
    iban: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Scheduling — Shifts, Schedules, Calendar, Holidays
# ─────────────────────────────────────────────────────────────────────────────
class ShiftOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    shift_type: Optional[str] = Field(None, description="morning, afternoon, night.")
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    break_min: Optional[int] = None
    tolerance_min: Optional[int] = None
    grace_period_min: Optional[int] = None
    is_split: Optional[bool] = None
    is_night: Optional[bool] = None
    is_rotativo: Optional[bool] = None
    plus_nocturnidad: Optional[float] = None
    plus_festividad: Optional[float] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ScheduleOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    employee_id: Optional[str] = None
    shift_id: Optional[str] = None
    date: Optional[str] = None
    notes: Optional[str] = None


class CalendarDayOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    year: Optional[int] = None
    date: Optional[str] = None
    day_type: Optional[str] = Field(None, description="working, weekend, holiday.")
    is_working_day: Optional[bool] = None
    is_holiday: Optional[bool] = None
    is_weekend: Optional[bool] = None
    holiday_name: Optional[str] = None


class CalendarGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    year: Optional[int] = None
    days_generated: Optional[int] = None


class HolidayOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    date: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = Field(None, description="national, regional, local.")
    region: Optional[str] = None
    locality: Optional[str] = None
    year: Optional[str] = None
    is_paid: Optional[bool] = None
    is_working: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# Contracts
# ─────────────────────────────────────────────────────────────────────────────
class ContractOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    employee_id: Optional[str] = None
    contract_type: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_indefinite: Optional[bool] = None
    weekly_hours: Optional[float] = None
    daily_hours: Optional[float] = None
    salary_base: Optional[float] = None
    status: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Vacations / Leave / Overtime
# ─────────────────────────────────────────────────────────────────────────────
class VacationRequestOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    type: Optional[str] = Field(None, description="vacation, personal, sick, etc.")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_days: Optional[float] = None
    status: Optional[str] = Field(None, description="pending, approved, rejected.")
    reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None


class LeaveOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    leave_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_days: Optional[int] = None
    status: Optional[str] = None
    diagnosis_code: Optional[str] = None
    mutua: Optional[str] = None
    is_work_accident: Optional[bool] = None


class OvertimeOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    date: Optional[str] = None
    overtime_type: Optional[str] = Field(None, description="structural, voluntary, force_majeure.")
    total_minutes: Optional[int] = None
    compensated_minutes: Optional[int] = None
    paid_minutes: Optional[int] = None
    overtime_amount: Optional[float] = None
    source: Optional[str] = Field(None, description="manual o auto.")


class OvertimeCalculateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    created: Optional[int] = None
    details: Optional[List[Dict[str, Any]]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Payroll
# ─────────────────────────────────────────────────────────────────────────────
class PayrollOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None
    base_salary: Optional[float] = None
    night_plus: Optional[float] = None
    holiday_plus: Optional[float] = None
    overtime_amount: Optional[float] = None
    gross_total: Optional[float] = None
    ss_deduction: Optional[float] = None
    irpf_deduction: Optional[float] = None
    net_total: Optional[float] = None
    status: Optional[str] = None


class PayrollCloseResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    month: Optional[int] = None
    year: Optional[int] = None
    status: Optional[str] = None
    message: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────────────────────────────────────────
class NotificationOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    recipient_type: Optional[str] = Field(None, description="employee o user.")
    employee_id: Optional[str] = None
    user_id: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    priority: Optional[str] = Field(None, description="normal, high, urgent.")
    category: Optional[str] = None
    is_read: Optional[bool] = None
    sent_at: Optional[str] = None
    read_at: Optional[str] = None


class UnreadCountResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    unread_count: int = Field(..., description="Número de notificaciones no leídas.")


class MarkAllReadResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Optional[str] = None
    marked_read: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# Incidents
# ─────────────────────────────────────────────────────────────────────────────
class IncidentOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    tenant_id: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    incident_type: Optional[str] = Field(
        None,
        description="no_clock_in, no_show, late, early_leave, ausencia_no_justificada, etc.",
    )
    date: Optional[str] = None
    description: Optional[str] = None
    is_resolved: Optional[bool] = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None


class IncidentDetectResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Optional[str] = None
    message: Optional[str] = None
    target_date: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Tenants / Settings
# ─────────────────────────────────────────────────────────────────────────────
class TenantOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    name: Optional[str] = None
    legal_name: Optional[str] = None
    cif: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    convenio: Optional[str] = None
    plan: Optional[str] = Field(None, description="basic, pro, kit.")
    max_employees: Optional[int] = None
    is_active: Optional[bool] = None
    tolerancia_min: Optional[int] = None
    setup_completed: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────────────────────────────────────
class HoursReportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    tenant_id: Optional[str] = None
    employees: Optional[List[Dict[str, Any]]] = None
    page: Optional[int] = None
    limit: Optional[int] = None
    total: Optional[int] = None
    pages: Optional[int] = None


class ExportJobAcceptedResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    job_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


class ExportStatusResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    job_id: Optional[str] = None
    status: Optional[str] = Field(None, description="pending, completed.")
    download_url: Optional[str] = None


class InspectionReportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    tenant: Optional[Dict[str, Any]] = None
    period: Optional[Dict[str, Any]] = None
    generated_at: Optional[str] = None
    legal_notice: Optional[str] = None
    employees: Optional[List[Dict[str, Any]]] = None
    summary: Optional[Dict[str, Any]] = None


class AbsenteeismReportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    period: Optional[Dict[str, Any]] = None
    global_absenteeism_rate: Optional[float] = None
    total_absence_days: Optional[int] = None
    total_possible_days: Optional[int] = None
    breakdown: Optional[Dict[str, Any]] = None
    employees: Optional[List[Dict[str, Any]]] = None
    top_5_absentees: Optional[List[Dict[str, Any]]] = None


class LaborCostsReportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    period: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    employees: Optional[List[Dict[str, Any]]] = None
    total_employees: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# Billing / Devices
# ─────────────────────────────────────────────────────────────────────────────
class CheckoutSessionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: Optional[str] = None
    session_id: Optional[str] = None


class PortalSessionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: Optional[str] = None


class DeviceResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    tenant_id: str
    device_token: str
    name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Optional[str] = Field(None, description="ok o degraded.")
    service: Optional[str] = None
    version: Optional[str] = None
    started_at: Optional[str] = None
    uptime_seconds: Optional[int] = None
    db_status: Optional[str] = None
    redis_status: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Examples for key endpoints
# ─────────────────────────────────────────────────────────────────────────────
EXAMPLES_LOGIN_REQUEST = {
    "value": {
        "email": "owner@latagliatella.es",
        "password": "secret123",
    },
    "summary": "Login de un owner",
    "description": "Credenciales de un usuario propietario de un restaurante.",
}

EXAMPLES_LOGIN_RESPONSE = {
    "value": {
        "ok": True,
        "user": {
            "id": "b3f1a2c4-...",
            "email": "owner@latagliatella.es",
            "role": "owner",
            "tenant_id": "a1b2c3d4-...",
            "name": "María García",
        },
        "tenant_id": "a1b2c3d4-...",
        "is_new_tenant": False,
    },
    "summary": "Login exitoso",
    "description": "Se devuelven los datos del usuario y el tenant. Los JWT se setean como cookies httpOnly.",
}

EXAMPLES_NFC_REQUEST = {
    "value": {
        "nfc_uid": "A1:B2:C3:D4",
        "tenant_id": "a1b2c3d4-...",
    },
    "summary": "Fichaje NFC",
    "description": "El terminal lee el UID de la tarjeta NFC del empleado y lo envía con el tenant_id.",
}

EXAMPLES_NFC_RESPONSE = {
    "value": {
        "ok": True,
        "message": "Carlos López — Entrada registrada",
        "type": "in",
        "employee_name": "Carlos López",
        "time": "2025-03-15T08:02:17+00:00",
        "clock": {
            "id": "clk-001-...",
            "tenant_id": "a1b2c3d4-...",
            "employee_id": "emp-001-...",
            "type": "in",
            "timestamp": "2025-03-15T08:02:17+00:00",
            "is_cancelled": False,
        },
    },
    "summary": "Fichaje NFC registrado",
    "description": "El tipo se determina automáticamente (auto-toggle) según el último fichaje del empleado.",
}

EXAMPLES_CREATE_EMPLOYEE_REQUEST = {
    "value": {
        "name": "Carlos",
        "last_name": "López",
        "dni": "12345678A",
        "phone": "+34 612 345 678",
        "email": "carlos.lopez@email.com",
        "categoria_profesional": "Camarero",
        "tipo_contrato": "indefinido",
        "tipo_jornada": "completa",
        "horas_semanales": 40,
        "pin": "1234",
        "nfc_uid": "A1:B2:C3:D4",
        "clock_method": "pin",
        "vacation_annual_days": 30,
        "estado": "activo",
        "is_active": True,
    },
    "summary": "Alta de empleado",
    "description": "Crea un camarero con PIN 1234 y tarjeta NFC asociada.",
}

EXAMPLES_CREATE_EMPLOYEE_RESPONSE = {
    "value": {
        "id": "emp-001-...",
        "tenant_id": "a1b2c3d4-...",
        "name": "Carlos",
        "last_name": "López",
        "full_name": "Carlos",
        "dni": "*****5678A",
        "phone": "*** 345 678",
        "email": "c***s@email.com",
        "categoria_profesional": "Camarero",
        "tipo_contrato": "indefinido",
        "estado": "activo",
        "is_active": True,
        "clock_method": "pin",
        "nfc_uid": "A1:B2:C3:D4",
        "vacation_annual_days": 30.0,
        "saldo_vacaciones": 30.0,
    },
    "summary": "Empleado creado",
    "description": "El DNI, teléfono e email se enmascaran por defecto (PII). El pin_hash nunca se expone.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Reusable responses dict builders
# ─────────────────────────────────────────────────────────────────────────────
def auth_responses() -> Dict[int, Dict[str, Any]]:
    """Common error responses for authenticated (JWT) endpoints."""
    return {
        401: {"description": "No autenticado — falta token JWT o cookie access_token, o token inválido/expirado.", "model": ErrorResponse},
        403: {"description": "Sin permisos suficientes (se requiere owner/manager/super_admin).", "model": ErrorResponse},
    }


def crud_responses(has_404: bool = True, has_400: bool = True) -> Dict[int, Dict[str, Any]]:
    """Standard error responses for CRUD endpoints with tenant-scoped access."""
    resp: Dict[int, Dict[str, Any]] = {}
    resp[401] = {"description": "No autenticado.", "model": ErrorResponse}
    resp[403] = {"description": "Acceso denegado (no pertenece al tenant o rol insuficiente).", "model": ErrorResponse}
    if has_404:
        resp[404] = {"description": "Recurso no encontrado.", "model": ErrorResponse}
    if has_400:
        resp[400] = {"description": "Solicitud inválida (validación de negocio o formato).", "model": ErrorResponse}
    resp[422] = {"description": "Error de validación de esquema (Pydantic).", "model": ValidationError}
    return resp