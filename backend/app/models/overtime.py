"""
TalentUP Fichaje — Overtime model (horas extra).

Security note: XSS escaping is applied once, in to_dict(), so API
responses are safe while raw values are preserved in the database.
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Date, DateTime, ForeignKey, Text, Index
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string/Text fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Overtime(Base):
    __tablename__ = "overtime"

    __table_args__ = (
        Index('ix_overtime_tenant_date', 'tenant_id', 'date'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    date = Column(Date, nullable=False)
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=True)

    overtime_type = Column(String(30), nullable=False)  # structural, force_majeure, voluntary, mandatory
    total_minutes = Column(Integer, nullable=False)
    compensated_minutes = Column(Integer, default=0)
    paid_minutes = Column(Integer, default=0)
    hourly_rate_multiplier = Column(Numeric(4, 2), default=1.75)

    hourly_rate = Column(Numeric(10, 2), nullable=True)
    overtime_amount = Column(Numeric(10, 2), nullable=True)

    compensation_type = Column(String(20), default="pending")  # pending, paid, compensated_with_rest
    compensated_date = Column(Date, nullable=True)
    payroll_id = Column(String(36), ForeignKey("payroll.id"), nullable=True)

    source = Column(String(30), default="auto")  # auto, manual
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "employee_id": str(self.employee_id) if self.employee_id else None,
            "date": self.date.isoformat() if self.date else None,
            "shift_id": str(self.shift_id) if self.shift_id else None,
            "overtime_type": _s(self.overtime_type),
            "total_minutes": self.total_minutes,
            "compensated_minutes": self.compensated_minutes,
            "paid_minutes": self.paid_minutes,
            "hourly_rate_multiplier": float(self.hourly_rate_multiplier) if self.hourly_rate_multiplier else None,
            "hourly_rate": float(self.hourly_rate) if self.hourly_rate else None,
            "overtime_amount": float(self.overtime_amount) if self.overtime_amount else None,
            "compensation_type": _s(self.compensation_type),
            "compensated_date": self.compensated_date.isoformat() if self.compensated_date else None,
            "payroll_id": str(self.payroll_id) if self.payroll_id else None,
            "source": _s(self.source),
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "notes": _s(self.notes),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
