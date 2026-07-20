"""
TalentUP Fichaje — Incident model (ampliado con 12 tipos de incidencia).

Security note: XSS escaping is applied once, in to_dict(), so API
responses are safe while raw values are preserved in the database.
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, Index, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string/Text fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Incident(Base):
    __tablename__ = "incidents"

    __table_args__ = (
        Index("ix_incident_tenant_type", "tenant_id", "incident_type"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    incident_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="warning")  # info, warning, critical

    # Contexto
    clock_in_id = Column(String(36), ForeignKey("clock_ins.id"), nullable=True)
    schedule_id = Column(String(36), ForeignKey("schedules.id"), nullable=True)
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=True)

    # Resolución
    is_resolved = Column(Boolean, default=False)
    resolution = Column(Text, nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Origen
    source = Column(String(20), default="auto")  # auto, manual, employee_report
    reported_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "employee_id": str(self.employee_id) if self.employee_id else None,
            "date": self.date.isoformat() if self.date else None,
            "incident_type": _s(self.incident_type),
            "description": _s(self.description),
            "severity": _s(self.severity),
            "clock_in_id": str(self.clock_in_id) if self.clock_in_id else None,
            "schedule_id": str(self.schedule_id) if self.schedule_id else None,
            "shift_id": str(self.shift_id) if self.shift_id else None,
            "is_resolved": self.is_resolved,
            "resolution": _s(self.resolution),
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "source": _s(self.source),
            "reported_by": str(self.reported_by) if self.reported_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
