"""
TalentUP Fichaje — Shift model (turnos ampliado con plus_nocturnidad, plus_festividad, is_rotativo).
"""
import uuid
import html
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Numeric, DateTime, ForeignKey, Time
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=True)
    shift_type = Column(String(30), default="morning")  # morning, afternoon, night, split, rotating, custom

    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_start = Column(Time, nullable=True)
    break_end = Column(Time, nullable=True)
    break_min = Column(Integer, default=0)
    total_hours = Column(Numeric(5, 2), nullable=True)

    tolerance_min = Column(Integer, default=5)
    grace_period_min = Column(Integer, default=15)
    overtime_threshold_min = Column(Integer, default=0)

    is_split = Column(Boolean, default=False)
    is_night = Column(Boolean, default=False)
    plus_nocturnidad = Column(Numeric(5, 2), default=0)  # % de plus de nocturnidad
    plus_festividad = Column(Numeric(5, 2), default=0)  # % de plus de festividad
    is_rotativo = Column(Boolean, default=False)

    color = Column(String(7), default="#FF6B35")
    icon = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "name": _s(self.name),
            "code": _s(self.code),
            "shift_type": _s(self.shift_type),
            "start_time": self.start_time.strftime("%H:%M") if self.start_time else None,
            "end_time": self.end_time.strftime("%H:%M") if self.end_time else None,
            "break_start": self.break_start.strftime("%H:%M") if self.break_start else None,
            "break_end": self.break_end.strftime("%H:%M") if self.break_end else None,
            "break_min": self.break_min,
            "total_hours": float(self.total_hours) if self.total_hours else None,
            "tolerance_min": self.tolerance_min,
            "grace_period_min": self.grace_period_min,
            "overtime_threshold_min": self.overtime_threshold_min,
            "is_split": self.is_split,
            "is_night": self.is_night,
            "plus_nocturnidad": float(self.plus_nocturnidad) if self.plus_nocturnidad else None,
            "plus_festividad": float(self.plus_festividad) if self.plus_festividad else None,
            "is_rotativo": self.is_rotativo,
            "color": _s(self.color),
            "icon": _s(self.icon),
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
