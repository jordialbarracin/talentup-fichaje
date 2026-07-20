"""
TalentUP Fichaje — Contract model (histórico de contratos).
"""
import uuid
import html
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Date, DateTime, ForeignKey, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    contract_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    duration_days = Column(Integer, nullable=True)
    is_indefinite = Column(Boolean, default=False)
    renewal_number = Column(Integer, default=0)
    previous_contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=True)

    work_day_type = Column(String(50), nullable=True)
    weekly_hours = Column(Numeric(5, 2), nullable=True)
    daily_hours = Column(Numeric(5, 2), nullable=True)
    salary_base = Column(Numeric(10, 2), nullable=True)
    salary_extras = Column(Numeric(10, 2), nullable=True)
    prorated_pages = Column(Numeric(10, 2), nullable=True)

    document_url = Column(Text, nullable=True)
    signed_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    status = Column(String(20), default="active")
    termination_date = Column(Date, nullable=True)
    termination_reason = Column(String(200), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "employee_id": str(self.employee_id) if self.employee_id else None,
            "contract_type": _s(self.contract_type),
            "category": _s(self.category),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration_days": self.duration_days,
            "is_indefinite": self.is_indefinite,
            "renewal_number": self.renewal_number,
            "previous_contract_id": str(self.previous_contract_id) if self.previous_contract_id else None,
            "work_day_type": _s(self.work_day_type),
            "weekly_hours": float(self.weekly_hours) if self.weekly_hours else None,
            "daily_hours": float(self.daily_hours) if self.daily_hours else None,
            "salary_base": float(self.salary_base) if self.salary_base else None,
            "salary_extras": float(self.salary_extras) if self.salary_extras else None,
            "prorated_pages": float(self.prorated_pages) if self.prorated_pages else None,
            "document_url": _s(self.document_url),
            "signed_date": self.signed_date.isoformat() if self.signed_date else None,
            "notes": _s(self.notes),
            "status": _s(self.status),
            "termination_date": self.termination_date.isoformat() if self.termination_date else None,
            "termination_reason": _s(self.termination_reason),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
