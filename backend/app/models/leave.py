"""
TalentUP Fichaje — Leave model (bajas médicas / ausencias).
Bajas IT (Incapacidad Temporal), permisos, ausencias.
"""
import uuid
import html
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Date, DateTime, ForeignKey, Text, Numeric, Index
from app.database import Base


def _s(value):
    """Escape string for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Leave(Base):
    __tablename__ = "leaves"

    __table_args__ = (
        Index('ix_leave_tenant_emp', 'tenant_id', 'employee_id'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    # Tipo de baja
    leave_type = Column(String(20), nullable=False)  # EC (enfermedad común), AT (accidente trabajo), EP (enfermedad profesional), maternity, permit
    type = Column(String(50), nullable=True)  # medical, personal, maternity, other (legacy compat)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    expected_end_date = Column(Date, nullable=True)
    total_days = Column(Integer, nullable=True)

    # Datos médicos (IT)
    diagnosis_code = Column(String(20), nullable=True)  # CIE-10
    medical_center = Column(String(200), nullable=True)
    doctor_name = Column(String(200), nullable=True)
    part_number = Column(String(50), nullable=True)  # PART-2026-XXX

    # Mutua / accidente
    mutua = Column(String(100), nullable=True)
    is_work_accident = Column(Boolean, default=False)
    is_professional_illness = Column(Boolean, default=False)
    has_leave_report = Column(Boolean, default=False)  # parte de baja

    reason = Column(Text, nullable=True)
    document_url = Column(Text, nullable=True)

    # Estado
    status = Column(String(20), default="active")  # active, completed, cancelled
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "employee_id": str(self.employee_id) if self.employee_id else None,
            "leave_type": _s(self.leave_type),
            "type": _s(self.type),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "expected_end_date": self.expected_end_date.isoformat() if self.expected_end_date else None,
            "total_days": self.total_days,
            "diagnosis_code": _s(self.diagnosis_code),
            "medical_center": _s(self.medical_center),
            "doctor_name": _s(self.doctor_name),
            "part_number": _s(self.part_number),
            "mutua": _s(self.mutua),
            "is_work_accident": self.is_work_accident,
            "is_professional_illness": self.is_professional_illness,
            "has_leave_report": self.has_leave_report,
            "reason": _s(self.reason),
            "document_url": _s(self.document_url),
            "status": _s(self.status),
            "is_active": self.is_active,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }