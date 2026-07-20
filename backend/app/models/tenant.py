"""
TalentUP Fichaje — Tenant model (ampliado con configuración convenio, vacaciones, billing).
"""
import uuid
import html
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Numeric, DateTime, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    legal_name = Column(String(200), nullable=True)
    cif = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)

    # Convenio
    convenio = Column(String(100), default="hosteleria")
    ccaa = Column(String(100), nullable=True)
    locality = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)

    # Config fichaje
    tolerancia_min = Column(Integer, default=5)
    default_grace_period = Column(Integer, default=15)
    auto_detect_incidents = Column(Boolean, default=True)
    require_geolocation = Column(Boolean, default=False)
    require_photo_on_clock = Column(Boolean, default=False)
    allow_offline_clock = Column(Boolean, default=True)
    max_offline_hours = Column(Integer, default=24)

    # Config vacaciones
    vacation_days_per_year = Column(Numeric(5, 2), default=30)
    vacation_accrual = Column(String(20), default="calendar")
    vacation_requires_approval = Column(Boolean, default=True)
    min_vacation_days_before = Column(Integer, default=15)
    max_consecutive_vacation_days = Column(Integer, default=30)

    # Config nómina
    payroll_day = Column(Integer, default=30)
    payroll_period = Column(String(20), default="monthly")
    irpf_default = Column(Numeric(5, 2), nullable=True)
    ss_employee_percent = Column(Numeric(5, 2), default=6.35)
    ss_company_percent = Column(Numeric(5, 2), default=29.90)

    # Plan / Billing
    plan = Column(String(20), default="basic")
    subscription_status = Column(String(20), default="active")
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    max_employees = Column(Integer, default=50)
    billing_email = Column(String(200), nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)

    # Estado
    is_active = Column(Boolean, default=True)
    setup_completed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": _s(self.name),
            "legal_name": _s(self.legal_name),
            "cif": _s(self.cif),
            "address": _s(self.address),
            "city": _s(self.city),
            "province": _s(self.province),
            "postal_code": _s(self.postal_code),
            "phone": _s(self.phone),
            "email": _s(self.email),
            "website": _s(self.website),
            "convenio": _s(self.convenio),
            "ccaa": _s(self.ccaa),
            "locality": _s(self.locality),
            "sector": _s(self.sector),
            "tolerancia_min": self.tolerancia_min,
            "default_grace_period": self.default_grace_period,
            "auto_detect_incidents": self.auto_detect_incidents,
            "require_geolocation": self.require_geolocation,
            "require_photo_on_clock": self.require_photo_on_clock,
            "allow_offline_clock": self.allow_offline_clock,
            "max_offline_hours": self.max_offline_hours,
            "vacation_days_per_year": float(self.vacation_days_per_year) if self.vacation_days_per_year else None,
            "vacation_accrual": _s(self.vacation_accrual),
            "vacation_requires_approval": self.vacation_requires_approval,
            "min_vacation_days_before": self.min_vacation_days_before,
            "max_consecutive_vacation_days": self.max_consecutive_vacation_days,
            "payroll_day": self.payroll_day,
            "payroll_period": _s(self.payroll_period),
            "irpf_default": float(self.irpf_default) if self.irpf_default else None,
            "ss_employee_percent": float(self.ss_employee_percent) if self.ss_employee_percent else None,
            "ss_company_percent": float(self.ss_company_percent) if self.ss_company_percent else None,
            "plan": _s(self.plan),
            "subscription_status": _s(self.subscription_status),
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "max_employees": self.max_employees,
            "billing_email": _s(self.billing_email),
            "stripe_customer_id": _s(self.stripe_customer_id),
            "stripe_subscription_id": _s(self.stripe_subscription_id),
            "is_active": self.is_active,
            "setup_completed": self.setup_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
