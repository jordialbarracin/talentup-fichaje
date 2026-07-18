"""
TalentUP Fichaje — Incident model (ampliado con 12 tipos de incidencia).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

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
            "incident_type": self.incident_type,
            "description": self.description,
            "severity": self.severity,
            "clock_in_id": str(self.clock_in_id) if self.clock_in_id else None,
            "schedule_id": str(self.schedule_id) if self.schedule_id else None,
            "shift_id": str(self.shift_id) if self.shift_id else None,
            "is_resolved": self.is_resolved,
            "resolution": self.resolution,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "source": self.source,
            "reported_by": str(self.reported_by) if self.reported_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
