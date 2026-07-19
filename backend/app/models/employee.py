"""
TalentUP Fichaje — Employee model (ampliado con 34 campos nuevos).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Date, DateTime, ForeignKey, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


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
            "employee_code": self.employee_code,
            "name": self.name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "dni": self.dni,
            "nie": self.nie,
            "numero_ss": self.numero_ss,
            "nationality": self.nationality,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "gender": self.gender,
            "address": self.address,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "phone": self.phone,
            "email": self.email,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "categoria_profesional": self.categoria_profesional,
            "tipo_contrato": self.tipo_contrato,
            "fecha_alta": self.fecha_alta.isoformat() if self.fecha_alta else None,
            "fecha_baja": self.fecha_baja.isoformat() if self.fecha_baja else None,
            "motivo_baja": self.motivo_baja,
            "tipo_jornada": self.tipo_jornada,
            "horas_semanales": float(self.horas_semanales) if self.horas_semanales else None,
            "horas_diarias": float(self.horas_diarias) if self.horas_diarias else None,
            "grupo_cotizacion": self.grupo_cotizacion,
            "base_cotizacion": float(self.base_cotizacion) if self.base_cotizacion else None,
            "seniority_date": self.seniority_date.isoformat() if self.seniority_date else None,
            "rehire_eligible": self.rehire_eligible,
            # "pin_hash": self.pin_hash,  # NEVER expose pin_hash in API responses
            "nfc_card_id": self.nfc_card_id,
            "nfc_uid": self.nfc_uid,
            "photo_url": self.photo_url,
            "fingerprint_hash": self.fingerprint_hash,
            "shift_id": str(self.shift_id) if self.shift_id else None,
            "clock_method": self.clock_method,
            "vacation_annual_days": float(self.vacation_annual_days) if self.vacation_annual_days else None,
            "vacation_days_used": float(self.vacation_days_used) if self.vacation_days_used else None,
            "saldo_vacaciones": float(self.saldo_vacaciones) if self.saldo_vacaciones else None,
            "vacation_year": self.vacation_year,
            "vacation_notes": self.vacation_notes,
            "saldo_banco_horas": float(self.saldo_banco_horas) if self.saldo_banco_horas else None,
            "horas_extra_pendientes": float(self.horas_extra_pendientes) if self.horas_extra_pendientes else None,
            "coste_hora": float(self.coste_hora) if self.coste_hora else None,
            "iban": self.iban,
            "bank_name": self.bank_name,
            "bank_account_holder": self.bank_account_holder,
            "education_level": self.education_level,
            "qualifications": self.qualifications,
            "food_handling_cert": self.food_handling_cert,
            "food_handling_expiry": self.food_handling_expiry.isoformat() if self.food_handling_expiry else None,
            "allergies": self.allergies,
            "uniform_size": self.uniform_size,
            "estado": self.estado,
            "is_active": self.is_active,
            "is_available_for_scheduling": self.is_available_for_scheduling,
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
