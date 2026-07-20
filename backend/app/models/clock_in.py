"""
TalentUP Fichaje — ClockIn model (fichajes).
Inmutable: no se editan, solo se cancelan con motivo.

Security note: XSS escaping is applied once, in to_dict(), so API
responses are safe while raw values are preserved in the database.
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey, Index, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string/Text fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class ClockIn(Base):
    __tablename__ = "clock_ins"

    __table_args__ = (
        Index("ix_clock_tenant_emp_time", "tenant_id", "employee_id", "timestamp"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)  # in, out, break_start, break_end
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_offline = Column(Boolean, default=False)
    synced_at = Column(DateTime(timezone=True), nullable=True)
    is_cancelled = Column(Boolean, default=False)
    cancel_reason = Column(Text, nullable=True)
    cancelled_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "employee_id": str(self.employee_id) if self.employee_id else None,
            "type": _s(self.type),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_offline": self.is_offline,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "is_cancelled": self.is_cancelled,
            "cancel_reason": _s(self.cancel_reason),
            "cancelled_by": str(self.cancelled_by) if self.cancelled_by else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }
