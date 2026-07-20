"""
TalentUP Fichaje — Employee model (ampliado con 34 campos nuevos).

Security note: XSS escaping is applied once, in to_dict(), so API
responses are safe while raw values are preserved in the database.
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Date, DateTime, ForeignKey, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string/Text fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_code = Column(String(20), nullable=True)

    # ===== DATOS PERSONALES =====
    name = Column(String(200), nullable=False)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    dni = Column(String(20), nullable=True)
    nie = Column(String(20), nullable=True)
    numero_ss = Column(String(20), nullable=True)
    nationality = Column(String(50), nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    # ===== DATOS LABORALES =====
    categoria_profesional = Column(String(100), nullable=True)
    tipo_contrato = Column(String(50), nullable=True)
    fecha_alta = Column(Date, nullable=True)
    fecha_baja = Column(Date, nullable=True)
    motivo_baja = Column(String(200), nullable=True)
    tipo_jornada = Column(String(50), nullable=True)
    horas_semanales = Column(Numeric(5, 2), nullable=True)
    horas_diarias = Column(Numeric(5, 2), nullable=True)
    grupo_cotizacion = Column(String(20), nullable=True)
    base_cotizacion = Column(Numeric(10, 2), nullable=True)
    seniority_date = Column(Date, nullable=True)
    rehire_eligible = Column(Boolean, default=True)

    # ===== DATOS DE FICHAJE =====
    pin_hash = Column(String(200), nullable=False)
    pin_hash_fast = Column(String(64), nullable=True, index=True)
    nfc_card_id = Column(String(100), nullable=True)
    nfc_uid = Column(String(50), nullable=True)
    photo_url = Column(Text, nullable=True)
    fingerprint_hash = Column(String(200), nullable=True)
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=True)
    clock_method = Column(String(20), default="pin")

    # ===== VACACIONES =====
    vacation_annual_days = Column(Numeric(5, 2), default=30)
    vacation_days_used = Column(Numeric(5, 2), default=0)
    saldo_vacaciones = Column(Numeric(5, 2), default=30)
    vacation_year = Column(Integer, nullable=True)
    vacation_notes = Column(Text, nullable=True)

    # ===== SALDOS =====
    saldo_banco_horas = Column(Numeric(10, 2), default=0)
    horas_extra_pendientes = Column(Numeric(10, 2), default=0)

    # ===== ECONÓMICO =====
    coste_hora = Column(Numeric(10, 2), nullable=True)
    iban = Column(String(34), nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_account_holder = Column(String(200), nullable=True)

    # ===== FORMACIÓN =====
    education_level = Column(String(100), nullable=True)
    qualifications = Column(Text, nullable=True)
    food_handling_cert = Column(Boolean, default=False)
    food_handling_expiry = Column(Date, nullable=True)
    allergies = Column(Text, nullable=True)
    uniform_size = Column(String(20), nullable=True)

    # ===== ESTADO =====
    estado = Column(String(20), default="activo")  # activo, baja, vacaciones, permiso
    is_active = Column(Boolean, default=True)
    is_available_for_scheduling = Column(Boolean, default=True)

    # ===== AUDITORÍA =====
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "employee_code": _s(self.employee_code),
            "name": _s(self.name),
            "last_name": _s(self.last_name),
            "full_name": _s(self.full_name),
            "dni": _s(self.dni),
            "nie": _s(self.nie),
            "numero_ss": _s(self.numero_ss),
            "nationality": _s(self.nationality),
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "gender": _s(self.gender),
            "address": _s(self.address),
            "city": _s(self.city),
            "province": _s(self.province),
            "postal_code": _s(self.postal_code),
            "phone": _s(self.phone),
            "email": _s(self.email),
            "emergency_contact_name": _s(self.emergency_contact_name),
            "emergency_contact_phone": _s(self.emergency_contact_phone),
            "categoria_profesional": _s(self.categoria_profesional),
            "tipo_contrato": _s(self.tipo_contrato),
            "fecha_alta": self.fecha_alta.isoformat() if self.fecha_alta else None,
            "fecha_baja": self.fecha_baja.isoformat() if self.fecha_baja else None,
            "motivo_baja": _s(self.motivo_baja),
            "tipo_jornada": _s(self.tipo_jornada),
            "horas_semanales": float(self.horas_semanales) if self.horas_semanales else None,
            "horas_diarias": float(self.horas_diarias) if self.horas_diarias else None,
            "grupo_cotizacion": _s(self.grupo_cotizacion),
            "base_cotizacion": float(self.base_cotizacion) if self.base_cotizacion else None,
            "seniority_date": self.seniority_date.isoformat() if self.seniority_date else None,
            "rehire_eligible": self.rehire_eligible,
            # "pin_hash": self.pin_hash,  # NEVER expose pin_hash in API responses
            "nfc_card_id": _s(self.nfc_card_id),
            "nfc_uid": _s(self.nfc_uid),
            "photo_url": _s(self.photo_url),
            "fingerprint_hash": _s(self.fingerprint_hash),
            "shift_id": str(self.shift_id) if self.shift_id else None,
            "clock_method": _s(self.clock_method),
            "vacation_annual_days": float(self.vacation_annual_days) if self.vacation_annual_days else None,
            "vacation_days_used": float(self.vacation_days_used) if self.vacation_days_used else None,
            "saldo_vacaciones": float(self.saldo_vacaciones) if self.saldo_vacaciones else None,
            "vacation_year": self.vacation_year,
            "vacation_notes": _s(self.vacation_notes),
            "saldo_banco_horas": float(self.saldo_banco_horas) if self.saldo_banco_horas else None,
            "horas_extra_pendientes": float(self.horas_extra_pendientes) if self.horas_extra_pendientes else None,
            "coste_hora": float(self.coste_hora) if self.coste_hora else None,
            "iban": _s(self.iban),
            "bank_name": _s(self.bank_name),
            "bank_account_holder": _s(self.bank_account_holder),
            "education_level": _s(self.education_level),
            "qualifications": _s(self.qualifications),
            "food_handling_cert": self.food_handling_cert,
            "food_handling_expiry": self.food_handling_expiry.isoformat() if self.food_handling_expiry else None,
            "allergies": _s(self.allergies),
            "uniform_size": _s(self.uniform_size),
            "estado": _s(self.estado),
            "is_active": self.is_active,
            "is_available_for_scheduling": self.is_available_for_scheduling,
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
