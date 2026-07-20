"""
TalentUP Fichaje — Payroll model (nóminas).

Security note: XSS escaping is applied once, in to_dict(), so API
responses are safe while raw values are preserved in the database.
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string/Text fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Payroll(Base):
    __tablename__ = "payroll"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    period_label = Column(String(20), nullable=True)

    contract_type = Column(String(50), nullable=True)
    professional_category = Column(String(100), nullable=True)
    work_day_type = Column(String(50), nullable=True)
    weekly_hours = Column(Numeric(5, 2), nullable=True)

    # Horas
    scheduled_hours = Column(Numeric(10, 2), default=0)
    worked_hours = Column(Numeric(10, 2), default=0)
    worked_days = Column(Integer, default=0)
    absent_days = Column(Integer, default=0)
    holiday_hours = Column(Numeric(10, 2), default=0)

    overtime_structural = Column(Numeric(10, 2), default=0)
    overtime_force_majeure = Column(Numeric(10, 2), default=0)
    overtime_total = Column(Numeric(10, 2), default=0)
    overtime_amount = Column(Numeric(10, 2), default=0)

    late_minutes = Column(Integer, default=0)
    early_leave_minutes = Column(Integer, default=0)
    no_show_days = Column(Integer, default=0)

    # Económico
    base_salary = Column(Numeric(10, 2), default=0)
    salary_prorated = Column(Numeric(10, 2), default=0)

    night_plus = Column(Numeric(10, 2), default=0)
    holiday_plus = Column(Numeric(10, 2), default=0)
    seniority_plus = Column(Numeric(10, 2), default=0)
    toxicity_plus = Column(Numeric(10, 2), default=0)
    responsibility_plus = Column(Numeric(10, 2), default=0)
    transport_plus = Column(Numeric(10, 2), default=0)
    meal_plus = Column(Numeric(10, 2), default=0)

    ss_deduction = Column(Numeric(10, 2), default=0)
    irpf_deduction = Column(Numeric(10, 2), default=0)
    other_deductions = Column(Numeric(10, 2), default=0)

    gross_total = Column(Numeric(10, 2), default=0)
    net_total = Column(Numeric(10, 2), default=0)

    status = Column(String(20), default="draft")  # draft, calculated, approved, paid
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(100), nullable=True)

    payroll_document_url = Column(Text, nullable=True)
    settlement_document_url = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "employee_id": str(self.employee_id) if self.employee_id else None,
            "year": self.year,
            "month": self.month,
            "period_label": _s(self.period_label),
            "contract_type": _s(self.contract_type),
            "professional_category": _s(self.professional_category),
            "work_day_type": _s(self.work_day_type),
            "weekly_hours": float(self.weekly_hours) if self.weekly_hours else None,
            "scheduled_hours": float(self.scheduled_hours) if self.scheduled_hours else None,
            "worked_hours": float(self.worked_hours) if self.worked_hours else None,
            "worked_days": self.worked_days,
            "absent_days": self.absent_days,
            "holiday_hours": float(self.holiday_hours) if self.holiday_hours else None,
            "overtime_structural": float(self.overtime_structural) if self.overtime_structural else None,
            "overtime_force_majeure": float(self.overtime_force_majeure) if self.overtime_force_majeure else None,
            "overtime_total": float(self.overtime_total) if self.overtime_total else None,
            "overtime_amount": float(self.overtime_amount) if self.overtime_amount else None,
            "late_minutes": self.late_minutes,
            "early_leave_minutes": self.early_leave_minutes,
            "no_show_days": self.no_show_days,
            "base_salary": float(self.base_salary) if self.base_salary else None,
            "salary_prorated": float(self.salary_prorated) if self.salary_prorated else None,
            "night_plus": float(self.night_plus) if self.night_plus else None,
            "holiday_plus": float(self.holiday_plus) if self.holiday_plus else None,
            "seniority_plus": float(self.seniority_plus) if self.seniority_plus else None,
            "toxicity_plus": float(self.toxicity_plus) if self.toxicity_plus else None,
            "responsibility_plus": float(self.responsibility_plus) if self.responsibility_plus else None,
            "transport_plus": float(self.transport_plus) if self.transport_plus else None,
            "meal_plus": float(self.meal_plus) if self.meal_plus else None,
            "ss_deduction": float(self.ss_deduction) if self.ss_deduction else None,
            "irpf_deduction": float(self.irpf_deduction) if self.irpf_deduction else None,
            "other_deductions": float(self.other_deductions) if self.other_deductions else None,
            "gross_total": float(self.gross_total) if self.gross_total else None,
            "net_total": float(self.net_total) if self.net_total else None,
            "status": _s(self.status),
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "payment_method": _s(self.payment_method),
            "payment_reference": _s(self.payment_reference),
            "payroll_document_url": _s(self.payroll_document_url),
            "settlement_document_url": _s(self.settlement_document_url),
            "notes": _s(self.notes),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
