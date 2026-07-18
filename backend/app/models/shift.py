"""
TalentUP Fichaje — Shift model (turnos).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Time
# UUID type: String(36) for SQLite compatibility
from app.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    tolerance_min = Column(Integer, default=5)
    is_split = Column(Boolean, default=False)
    break_min = Column(Integer, default=0)
    color = Column(String(7), default="#FF6B35")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "name": self.name,
            "start_time": self.start_time.strftime("%H:%M") if self.start_time else None,
            "end_time": self.end_time.strftime("%H:%M") if self.end_time else None,
            "tolerance_min": self.tolerance_min,
            "is_split": self.is_split,
            "break_min": self.break_min,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
