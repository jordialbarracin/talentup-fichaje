"""
TalentUP Fichaje — VacationRequest model (solicitudes de vacaciones/permisos).
"""
import uuid
import html
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Numeric, Date, DateTime, ForeignKey, Text, Index
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class VacationRequest(Base):
    __tablename__ = "vacation_requests"

    __table_args__ = (
        Index('ix_vacation_tenant_status', 'tenant_id', 'status'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    type = Column(String(30), nullable=False)  # vacation, personal_leave, unpaid_leave, maternity, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Numeric(5, 2), nullable=False)
    days_count_method = Column(String(20), default="working")  # working, calendar

    reason = Column(Text, nullable=True)
    supporting_doc_url = Column(Text, nullable=True)

    status = Column(String(20), default="pending")  # pending, approved, rejected, cancelled
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "employee_id": str(self.employee_id) if self.employee_id else None,
            "type": _s(self.type),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_days": float(self.total_days) if self.total_days else None,
            "days_count_method": _s(self.days_count_method),
            "reason": _s(self.reason),
            "supporting_doc_url": _s(self.supporting_doc_url),
            "status": _s(self.status),
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": _s(self.rejection_reason),
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
